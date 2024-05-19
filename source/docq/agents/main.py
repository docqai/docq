"""Agents."""
import logging
import os
import time
from typing import Dict, List, Optional

import semantic_kernel

# from autogen import AssistantAgent, UserProxyAgent
from docq.model_selection.main import ModelCapability, get_model_settings_collection
from opentelemetry import trace
from semantic_kernel.core_skills import ConversationSummarySkill, TextSkill, TimeSkill

from ..domain import Assistant
from ..llm_plugins.openai.sk_bing_plugin import BingPlugin
from ..llm_plugins.openai.sk_web_pages_plugin import WebPagesPlugin
from ..llm_plugins.openai.weather_plugin import WeatherPlugin
from .assistant_agent import AssistantAgent

# from .assistant_agent import AssistantAgent
from .datamodels import Message
from .semantic_kernel_utils import (
    ASSISTANT_PERSONA,
    generate_autogen_llm_config,
    get_autogen_function_map,
)
from .user_proxy_agent import UserProxyAgent

# from .user_proxy_agent import UserProxyAgent
from .utils import (
    extract_last_useful_message,
    extract_successful_code_blocks,
    get_autogen_llm_config,
    get_modified_files,
    init_webserver_folders,
    md5_hash,
)

# Load LLM inference endpoints from an env variable or a file
# See https://microsoft.github.io/autogen/docs/FAQ#set-your-api-endpoints
# and OAI_CONFIG_LIST_sample
# config_list = config_list_from_json(env_or_file="OAI_CONFIG_LIST")

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)
config_list: List[Dict[str, str]] = []

chat_model_settings = get_model_settings_collection("azure_openai_latest").model_usage_settings[ModelCapability.CHAT]

config_list.append(get_autogen_llm_config(chat_model_settings))

# You can also set config_list directly as a list, for example, config_list = [{'model': 'gpt-4', 'api_key': '<your OpenAI API key here>'},]

DEFAULT_SYSTEM_MESSAGE = """You are a helpful AI assistant.
Solve tasks using your coding and language skills.
In the following cases, suggest python code (in a python coding block) or shell script (in a sh coding block) for the user to execute.
    1. When you need to collect info, use the code to output the info you need, for example, browse or search the web, 
    download/read a file, print the content of a webpage or a file, get the current date/time, check the operating system. 
    After sufficient info is printed and the task is ready to be solved based on your language skill, you can solve the task by yourself.
    2. When you need to perform some task with code, use the code to perform the task and output the result. Finish the task smartly.
Solve the task step by step if you need to. If a plan is not provided, explain your plan first. Be clear which step uses code, and which step uses your language skill.
When using code, you must properly format code blocks in code fences and indicate the code language like python or sh. 
ONLY format executable code in code fences. NEVER format instructions or output examples in code fences.
DO NOT suggest code that uses services that require authentication or API keys or other credentials.
The user cannot provide any other feedback or perform any other action beyond executing the code you suggest. 
The user can't modify your code. So do not suggest incomplete code which requires users to modify. Don't use a code block if it's not intended to be executed by the user.
The output of code execution should only be json formatted data including metadata to artifacts generated like images for charts. 
Dot not open images or any files with external programs like plt.show().
If you want the user to save the code in a file before executing it, put # filename: <filename> inside the code block as the first line. 
Don't include multiple code blocks in one response. Do not ask users to copy and paste the result. Instead, use 'print' function for the output when relevant. 
Check the execution result returned by the user.
If the result indicates there is an error, fix the error and output the code again. Suggest the full code instead of partial code or code changes. 
If the error can't be fixed or if the task is not solved even after the code is executed successfully, analyze the problem, revisit your assumption, 
collect additional info you need, and think of a different approach to try.
When you find an answer, verify the answer carefully. Include verifiable evidence in your response if possible.
Reply "TERMINATE" in the end when everything is done.
    """

folders = init_webserver_folders("./.persisted/agents/")


USER_PROXY_INSTRUCTIONS = """If the request has been addressed sufficiently, summarize the answer and end with the word TERMINATE. Otherwise, ask a follow-up question."""

current_user_id_thread_id = "user_id_plus_threadid_goes_here_12345"
user_dir = os.path.join(folders["files_static_root"], "user", md5_hash(current_user_id_thread_id))
os.makedirs(user_dir, exist_ok=True)
scratch_dir = os.path.join(user_dir, "scratch")


# DEFAULT_AGENT_REQUEST = "Plot a chart of NVDA and TESLA stock price YTD. Save the result to a file named nvda_tesla.png"
DEFAULT_AGENT_REQUEST = "What's the weather in London today?"

@tracer.start_as_current_span("run_agent")
def run_agent(
    user_request_message: str = DEFAULT_AGENT_REQUEST, assistant: Optional[Assistant] = None
) -> Message:  # Dict[Agent, List[Dict]]: #List[dict]:
    """Run the agent."""
    bing_search_api_key = os.getenv("DOCQ_BING_SEARCH_API_KEY") or ""
    kernel = semantic_kernel.Kernel()
    kernel.import_skill(BingPlugin(bing_search_api_key))
    kernel.import_skill(WebPagesPlugin())
    kernel.import_skill(WeatherPlugin())
    #kernel.import_skill(ConversationSummarySkill(kernel), "conversation_summary")
    # kernel.import_skill(HttpSkill(), "http")
    kernel.import_skill(TextSkill(), "text")
    kernel.import_skill(TimeSkill(), "time")

    assistant_agent = AssistantAgent(
        name=assistant.name if assistant else "General Assistant 1",
        llm_config=generate_autogen_llm_config(chat_model_settings, kernel),
        system_message=assistant.system_message_content if assistant else ASSISTANT_PERSONA,
    )

    worker = UserProxyAgent(
        "worker",
        #code_execution_config={"work_dir": scratch_dir, "use_docker": False},
        code_execution_config=False,
        human_input_mode="NEVER",
        llm_config=get_autogen_llm_config(chat_model_settings),
        # default_auto_reply="make sure code is properly formatted with code fences. If the result was generated correctly then terminate.",
        max_consecutive_auto_reply=5,
        function_map=get_autogen_function_map(kernel),
        system_message=USER_PROXY_INSTRUCTIONS,
    )


    start_time = time.time()
    worker.initiate_chat(
        assistant_agent,
        message=user_request_message,
    )

    metadata = {}
    agent_chat_messages = worker.chat_messages[assistant_agent]  # [len(history) :]
    metadata["messages"] = agent_chat_messages

    successful_code_blocks = extract_successful_code_blocks(agent_chat_messages)
    successful_code_blocks = "\n\n".join(successful_code_blocks)
    last_message = extract_last_useful_message(agent_chat_messages)

    print("Last message: ", last_message)

    print("Successful code blocks: ", successful_code_blocks)
    output = "<empty>"
    if last_message:
        output = (
            (last_message["content"] + "\n" + successful_code_blocks)
            if successful_code_blocks
            else last_message["content"]
        )

    metadata["code"] = ""
    end_time = time.time()
    metadata["time"] = end_time - start_time
    modified_files = get_modified_files(
        start_timestamp=start_time, end_timestamp=end_time, source_dir=scratch_dir, dest_dir=user_dir
    )
    metadata["files"] = modified_files

    print("Modified files: ", len(modified_files))

    output_message = Message(
        user_id="2",
        root_msg_id="1",
        role="assistant",
        content=output,
        metadata=metadata,
        session_id="3",
    )

    return output_message

    # return user_proxy.chat_messages
