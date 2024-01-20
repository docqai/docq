"""Agents."""
import json
import logging
import os
import time
from dataclasses import asdict
from typing import Any, Callable, Dict, List, Literal, Optional, Self, Tuple, Union

import autogen
from autogen import Agent, AssistantAgent, ConversableAgent, UserProxyAgent
from docq.model_selection.main import ModelCapability, get_model_settings_collection
from httpx import get
from numpy import rec

from .datamodels import AgentConfig, AgentFlowSpec, AgentWorkFlowConfig, LLMConfig, Message
from .utils import extract_successful_code_blocks, get_default_agent_config, get_modified_files

# Load LLM inference endpoints from an env variable or a file
# See https://microsoft.github.io/autogen/docs/FAQ#set-your-api-endpoints
# and OAI_CONFIG_LIST_sample
# config_list = config_list_from_json(env_or_file="OAI_CONFIG_LIST")

logger = logging.getLogger(__name__)

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


# def run_agent() -> str:
#     """Run the agent."""
#     # assistant = AssistantAgent("assistant", llm_config={"config_list": config_list})
#     # user_proxy = UserProxyAgent("user_proxy", code_execution_config={"work_dir": "coding"})
#     # user_proxy.initiate_chat(assistant, message="Plot a chart of NVDA and TESLA stock price change YTD.")
#     # This initiates an automated chat between the two agents to solve the task

#     user_proxy_config = AgentConfig(name="user_proxy")
#     assistant_config = AgentConfig(name="assistant", llm_config=LLMConfig(config_list=config_list))
#     flow_config = AgentWorkFlowConfig(name="default", sender=AgentFlowSpec(type="userproxy", config=user_proxy_config), receiver=AgentFlowSpec(type="assistant", config=assistant_config))

#     # workflow_manager = AutoGenWorkFlowManager(config=flow_config)
#     # workflow_manager.run("Plot a chart of NVDA and TESLA stock price change YTD.")

#     m = Message(content="Plot a chart of NVDA and TESLA stock price change YTD.",user_id="user_proxy",role="user",root_msg_id="root",session_id="session")

#     return AutoGenChatManager().chat(message=m, flow_config=flow_config, history=[], work_dir="./.persisted/agents/coding")


def handle_messages(
    recipient: ConversableAgent,
    messages: Optional[List[Dict]] = None,
    sender: Optional[Agent] = None,
    config: Optional[Any] = None,
) -> Tuple[bool, Union[str, Dict, None]]:
    """Handle messages from the sender."""
    logging.debug("Received messages: s%", messages)
    return False, None


class DocqUserProxyAgent(UserProxyAgent):
    """DocqUserProxy class."""

    def __init__(
        self: Self,
        name: str,
        is_termination_msg: Optional[Callable[[Dict], bool]] = None,
        max_consecutive_auto_reply: Optional[int] = None,
        human_input_mode: Optional[str] = "ALWAYS",
        function_map: Optional[Dict[str, Callable]] = None,
        code_execution_config: Optional[Union[Dict, Literal[False]]] = None,  # noqa: F821
        default_auto_reply: Optional[Union[str, Dict, None]] = "",
        llm_config: Optional[Union[Dict, Literal[False]]] = False,
        system_message: Optional[str] = "",
        receive_callback: Optional[Callable] = None,
        send_callback: Optional[Callable] = None,
    ) -> None:
        """Initialize the DocqUserProxy class.

        Args:
            name: The name of the agent.
            is_termination_msg: A function that returns True if the message is a termination message.
            max_consecutive_auto_reply: The maximum number of consecutive auto replies.
            human_input_mode: The human input mode.
            function_map: The function map.
            code_execution_config: The code execution configuration.
            default_auto_reply: The default auto reply.
            llm_config: The LLM configuration.
            system_message: The system message.
            receive_callback: The receive callback function. Signature:
                            def func(
                                self: Self,
                                message: Dict | str,
                                recipient: Agent,
                                request_reply: bool | None = None,
                                silent: bool | None = False,
                            ) -> None:
            send_callback: The send callback function. Signature:
                          def func(
                            self: Self,
                            message: Dict | str,
                            recipient: Agent,
                            request_reply: bool | None = None,
                            silent: bool | None = False,
                        ) -> None:
        """
        self.receive_callback = receive_callback
        self.send_callback = send_callback

        super().__init__(
            name=name,
            is_termination_msg=is_termination_msg,
            max_consecutive_auto_reply=max_consecutive_auto_reply,
            human_input_mode=human_input_mode,
            function_map=function_map,
            code_execution_config=code_execution_config,
            llm_config=llm_config,
            default_auto_reply=default_auto_reply,
            system_message=system_message
        )

    def receive(
        self: Self, message: Dict | str, sender: Agent, request_reply: bool | None = None, silent: bool | None = False
    ) -> None:
        """Receive a message from another agent aka the `sender`."""
        if self.receive_callback:
            self.receive_callback(message, sender, request_reply, silent)
        super().receive(message, sender, request_reply, silent)

    def send(
        self: Self,
        message: Union[Dict, str],
        recipient: Agent,
        request_reply: Optional[bool] = None,
        silent: Optional[bool] = False,
    ) -> None:
        """Send a message to another agent aka the `recipient`."""
        if self.send_callback:
            self.send_callback(message, recipient, request_reply, silent)
        super().send(message, recipient, request_reply, silent)

    async def a_receive(
        self: Self, message: Dict | str, sender: Agent, request_reply: bool | None = None, silent: bool | None = False
    ) -> None:
        """Async receive a message from another agent aka the `sender`."""
        if self.receive_callback:
            self.receive_callback(message, sender, request_reply, silent)
        await super().a_receive(message, sender, request_reply, silent)

    async def a_send(
        self: Self,
        message: Union[Dict, str],
        recipient: Agent,
        request_reply: Optional[bool] = None,
        silent: Optional[bool] = False,
    ) -> None:
        """Async send a message to another agent aka the `recipient`."""
        if self.send_callback:
            self.send_callback(message, recipient, request_reply, silent)
        await super().a_send(message, recipient, request_reply, silent)


def run_agent(message_receive_callback_handler: Callable, message_send_callback_handler: Callable) -> Dict[Agent, List[Dict]]:
    """Run the agent."""
    assistant = AssistantAgent("assistant1", llm_config={"config_list": config_list})
    user_proxy = UserProxyAgent(
        "user_proxy1",
        code_execution_config={"work_dir": "./.persisted/agents/coding"},
        human_input_mode="NEVER",
        max_consecutive_auto_reply=10,
    )
    user_proxy.initiate_chat(assistant, message="Plot a chart of NVDA and TESLA stock price change YTD.")

    # This initiates an automated chat between the two agents to solve the task
    logger.debug("===========================")
    logger.debug(assistant.last_message(user_proxy))
    logger.debug(user_proxy.last_message(assistant))
    logger.debug("===========================")
    # user_proxy.register_reply(assistant, handle_messages)how do

    # return AutoGenChatManager().chat(message=m, flow_config=flow_config, history=[], work_dir="./.persisted/agents/coding")
    return user_proxy.chat_messages

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
