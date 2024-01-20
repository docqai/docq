"""Agents."""
import json
import logging
import os
import time
from dataclasses import asdict
from typing import Any, Callable, Dict, List, Literal, Optional, Self, Tuple, Union

import autogen
from autogen import Agent
from colorama import init
from docq.model_selection.main import ModelCapability, get_model_settings_collection
from opentelemetry import trace

from .assistant_agent import AssistantAgent
from .conversable_agent import ConversableAgent
from .datamodels import AgentConfig, AgentFlowSpec, AgentWorkFlowConfig, LLMConfig, Message
from .user_proxy_agent import UserProxyAgent
from .utils import (
    extract_last_useful_message,
    extract_successful_code_blocks,
    get_all_skills,
    get_default_agent_config,
    get_modified_files,
    get_skills_prompt,
    init_webserver_folders,
    md5_hash,
    skill_from_folder,
)

# Load LLM inference endpoints from an env variable or a file
# See https://microsoft.github.io/autogen/docs/FAQ#set-your-api-endpoints
# and OAI_CONFIG_LIST_sample
# config_list = config_list_from_json(env_or_file="OAI_CONFIG_LIST")

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)
config_list: List[Dict[str, str]] = []

chat_model_settings = get_model_settings_collection("azure_openai_latest").model_usage_settings[ModelCapability.CHAT]

config_list.append(
    {
        "model": chat_model_settings.model_deployment_name.__str__(),
        "api_key": os.getenv("DOCQ_AZURE_OPENAI_API_KEY1") or "",
        "base_url": os.getenv("DOCQ_AZURE_OPENAI_API_BASE") or "",
        "api_type": "azure",
        "api_version": os.getenv("DOCQ_AZURE_OPENAI_API_VERSION") or "2023-07-01-preview",
    }
)

# You can also set config_list directly as a list, for example, config_list = [{'model': 'gpt-4', 'api_key': '<your OpenAI API key here>'},]

DEFAULT_SYSTEM_MESSAGE = """You are a helpful AI assistant.
Solve tasks using your coding and language skills.
In the following cases, suggest python code (in a python coding block) or shell script (in a sh coding block) for the user to execute.
    1. When you need to collect info, use the code to output the info you need, for example, browse or search the web, download/read a file, print the content of a webpage or a file, get the current date/time, check the operating system. After sufficient info is printed and the task is ready to be solved based on your language skill, you can solve the task by yourself.
    2. When you need to perform some task with code, use the code to perform the task and output the result. Finish the task smartly.
Solve the task step by step if you need to. If a plan is not provided, explain your plan first. Be clear which step uses code, and which step uses your language skill.
When using code, you must properly format code blocks in code fences and indicate the code language like python or sh. The user cannot provide any other feedback or perform any other action beyond executing the code you suggest. The user can't modify your code. So do not suggest incomplete code which requires users to modify. Don't use a code block if it's not intended to be executed by the user.
The output of code execution should only be json formatted data including metadata to artifacts generated like images for charts. Dot not open images or any files with external programs like plt.show().
If you want the user to save the code in a file before executing it, put # filename: <filename> inside the code block as the first line. Don't include multiple code blocks in one response. Do not ask users to copy and paste the result. Instead, use 'print' function for the output when relevant. Check the execution result returned by the user.
If the result indicates there is an error, fix the error and output the code again. Suggest the full code instead of partial code or code changes. If the error can't be fixed or if the task is not solved even after the code is executed successfully, analyze the problem, revisit your assumption, collect additional info you need, and think of a different approach to try.
When you find an answer, verify the answer carefully. Include verifiable evidence in your response if possible.
Reply "TERMINATE" in the end when everything is done.
    """

folders = init_webserver_folders("./.persisted/agents/")

USER_PROXY_INSTRUCTIONS = """If the request has been addressed sufficiently, summarize the answer and end with the word TERMINATE. Otherwise, ask a follow-up question.
        """

current_user_id_thread_id = "user_id_plus_threadid_goes_here_12345"
user_dir = os.path.join(folders["files_static_root"], "user", md5_hash(current_user_id_thread_id))
os.makedirs(user_dir, exist_ok=True)
skills = get_all_skills(
        os.path.join(folders["user_skills_dir"], md5_hash(current_user_id_thread_id)),
        folders["global_skills_dir"],
        dest_dir=os.path.join(user_dir, "scratch"),
    )

skills_suffix = get_skills_prompt(skills)

DEFAULT_AGENT_REQUEST = "Plot a chart of NVDA and TESLA stock price YTD. Save the result to a file named nvda_tesla.png"

@tracer.start_as_current_span("run_agent")
def run_agent(user_request_message: str = DEFAULT_AGENT_REQUEST) -> Message: #Dict[Agent, List[Dict]]: #List[dict]:
    """Run the agent."""
    assistant = AssistantAgent(
        "assistant1",
        llm_config={"config_list": config_list},
        system_message=autogen.AssistantAgent.DEFAULT_SYSTEM_MESSAGE + skills_suffix,
    )

    scratch_dir = os.path.join(user_dir, "scratch")
    user_proxy = UserProxyAgent(
        "user_proxy1",
        code_execution_config={"work_dir": scratch_dir},
        human_input_mode="NEVER",
        # default_auto_reply="make sure code is properly formatted with code fences. If the result was generated correctly then terminate.",
        max_consecutive_auto_reply=15,
        system_message=USER_PROXY_INSTRUCTIONS,
        is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    )

    start_time = time.time()
    user_proxy.initiate_chat(
        assistant,
        message=user_request_message,
    )
    #return user_proxy._agent_log
    metadata = {}
    agent_chat_messages = user_proxy.chat_messages[assistant] #[len(history) :]
    metadata["messages"] = agent_chat_messages

    successful_code_blocks = extract_successful_code_blocks(agent_chat_messages)
    successful_code_blocks = "\n\n".join(successful_code_blocks)
    last_message = extract_last_useful_message(agent_chat_messages)
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
    modified_files = get_modified_files(start_timestamp=start_time, end_timestamp=end_time, source_dir=scratch_dir, dest_dir=user_dir)
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

    #return user_proxy.chat_messages


class AutoGenChatManager:
    def __init__(self) -> None:
        pass

    def chat(self, message: Message, history: List, flow_config: AgentWorkFlowConfig = None, **kwargs) -> str:
        work_dir = kwargs.get("work_dir", None)
        scratch_dir = os.path.join(work_dir, "scratch")
        skills_suffix = kwargs.get("skills_prompt", "")

        # if no flow config is provided, use the default
        if flow_config is None:
            flow_config = get_default_agent_config(scratch_dir, skills_suffix=skills_suffix)

        # print("Flow config: ", flow_config)
        flow = AutoGenWorkFlowManager(
            config=flow_config, history=history, work_dir=scratch_dir, assistant_prompt=skills_suffix
        )
        message_text = message.content.strip()

        output = ""
        start_time = time.time()

        metadata = {}
        flow.run(message=f"{message_text}", clear_history=False)

        agent_chat_messages = flow.receiver.chat_messages[flow.sender][len(history) :]
        metadata["messages"] = agent_chat_messages

        successful_code_blocks = extract_successful_code_blocks(agent_chat_messages)
        successful_code_blocks = "\n\n".join(successful_code_blocks)
        output = (
            (flow.sender.last_message()["content"] + "\n" + successful_code_blocks)
            if successful_code_blocks
            else flow.sender.last_message()["content"]
        )

        metadata["code"] = ""
        end_time = time.time()
        metadata["time"] = end_time - start_time
        modified_files = get_modified_files(start_time, end_time, scratch_dir, dest_dir=work_dir)
        metadata["files"] = modified_files

        print("Modified files: ", len(modified_files))

        output_message = Message(
            user_id=message.user_id,
            root_msg_id=message.root_msg_id,
            role="assistant",
            content=output,
            metadata=json.dumps(metadata),
            session_id=message.session_id,
        )
        logging.debug("Output message: %s", output_message.content)
        return output_message.content


class AutoGenWorkFlowManager:
    """AutoGenWorkFlowManager class to load agents from a provided configuration and run a chat between them."""

    def __init__(
        self: Self,
        config: AgentWorkFlowConfig,
        history: Optional[List[Message]] = None,
        work_dir: str = None,
        assistant_prompt: str = None,
    ) -> None:
        """Initializes the AutoGenFlow with agents specified in the config and optional message history.

        Args:
            config: The configuration settings for the sender and receiver agents.
            history: An optional list of previous messages to populate the agents' history.
            work_dir: The working directory for the code execution agent.
            assistant_prompt: The assistant prompt for the code execution agent.
        """
        self.work_dir = work_dir or "work_dir"
        self.assistant_prompt = assistant_prompt or ""
        self.sender = self.load(config.sender)
        self.receiver = self.load(config.receiver)

        if history:
            self.populate_history(history)

    def _sanitize_history_message(self: Self, message: str) -> str:
        """Sanitizes the message e.g. remove references to execution completed.

        Args:
            message: The message to be sanitized.

        Returns:
            The sanitized message.
        """
        to_replace = ["execution succeeded", "exitcode"]
        for replace in to_replace:
            message = message.replace(replace, "")
        return message

    def populate_history(self: Self, history: List[Message]) -> None:
        """Populates the agent message history from the provided list of messages.

        Args:
            history: A list of messages to populate the agents' history.
        """
        for msg in history:
            if isinstance(msg, dict):
                msg = Message(**msg)
            if msg.role == "user":
                self.sender.send(
                    msg.content,
                    self.receiver,
                    request_reply=False,
                )
            elif msg.role == "assistant":
                self.receiver.send(
                    msg.content,
                    self.sender,
                    request_reply=False,
                )

    def sanitize_agent_spec(self: Self, agent_spec: AgentFlowSpec) -> AgentFlowSpec:
        """Sanitizes the agent spec by setting loading defaults.

        Args:
            agent_spec: The specification of the agent to be loaded.

        Returns:
            The sanitized agent configuration.
        """
        agent_spec.config.is_termination_msg = agent_spec.config.is_termination_msg or (
            lambda x: "TERMINATE" in x.get("content", "").rstrip()
        )

        if agent_spec.type == "userproxy":
            code_execution_config = agent_spec.config.code_execution_config or {}
            code_execution_config["work_dir"] = self.work_dir
            agent_spec.config.code_execution_config = code_execution_config

        if agent_spec.type == "assistant":
            agent_spec.config.system_message = f"{autogen.AssistantAgent.DEFAULT_SYSTEM_MESSAGE} \
            \n\n{agent_spec.config.system_message} \
            \n\n {self.assistant_prompt}"

        return agent_spec

    def load(self: Self, agent_spec: AgentFlowSpec) -> autogen.Agent:
        """Loads an agent based on the provided agent specification.

        Args:
            agent_spec: The specification of the agent to be loaded.

        Returns:
            An instance of the loaded agent.
        """
        agent: autogen.Agent
        agent_spec = self.sanitize_agent_spec(agent_spec)
        if agent_spec.type == "assistant":
            agent = autogen.AssistantAgent(**asdict(agent_spec.config))
        elif agent_spec.type == "userproxy":
            agent = autogen.UserProxyAgent(**asdict(agent_spec.config))
        else:
            raise ValueError(f"Unknown agent type: {agent_spec.type}")
        return agent

    def run(self: Self, message: str, clear_history: bool = False) -> None:
        """Initiates a chat between the sender and receiver agents with an initial message and an option to clear the history.

        Args:
            message: The initial message to start the chat.
            clear_history: If set to True, clears the chat history before initiating.
        """
        self.sender.initiate_chat(
            self.receiver,
            message=message,
            clear_history=clear_history,
        )
