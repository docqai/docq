"""Agent related utils."""

import ast
import base64
import hashlib
import logging
import os
import re
import shutil
from typing import Dict, List, Tuple, Union

from ..model_selection.main import LlmUsageSettings


def get_autogen_llm_config(chat_model_settings: LlmUsageSettings) -> Dict[str, str]:
    """Get the default LLM config for Autogen.

    :return: A list of dictionaries containing the LLM config for Autogen.
    """
    sc = chat_model_settings.service_instance_config

    return {
            "model": sc.model_deployment_name.__str__(),
            "api_key":  sc.api_key or "",
            "base_url": sc.api_base or "",
            "api_type": sc.api_type or "azure",
            "api_version": "2023-07-01-preview" #"2023-10-01-preview",
        }


def md5_hash(text: str) -> str:
    """Compute the MD5 hash of a given text.

    :param text: The string to hash
    :return: The MD5 hash of the text
    """
    return hashlib.md5(text.encode()).hexdigest()


def get_file_type(file_path: str) -> str:
    """Get file type   determined by the file extension. If the file extension is not recognized, 'unknown' will be used as the file type.

    :param file_path: The path to the file to be serialized.
    :return: A  string containing the file type.
    """
    # Extended list of file extensions for code and text files
    CODE_EXTENSIONS = {
        ".py",
        ".js",
        ".jsx",
        ".java",
        ".c",
        ".cpp",
        ".cs",
        ".ts",
        ".tsx",
        ".html",
        ".css",
        ".scss",
        ".less",
        ".json",
        ".xml",
        ".yaml",
        ".yml",
        ".md",
        ".rst",
        ".tex",
        ".sh",
        ".bat",
        ".ps1",
        ".php",
        ".rb",
        ".go",
        ".swift",
        ".kt",
        ".hs",
        ".scala",
        ".lua",
        ".pl",
        ".sql",
        ".config",
    }

    # Supported image extensions
    IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".svg", ".webp"}

    # Supported PDF extension
    PDF_EXTENSION = ".pdf"

    # Determine the file extension
    _, file_extension = os.path.splitext(file_path)

    # Determine the file type based on the extension
    if file_extension in CODE_EXTENSIONS:
        file_type = "code"
    elif file_extension in IMAGE_EXTENSIONS:
        file_type = "image"
    elif file_extension == PDF_EXTENSION:
        file_type = "pdf"
    else:
        file_type = "unknown"

    return file_type


def serialize_file(file_path: str) -> Tuple[str, str]:
    """Reads a file from a given file path, base64 encodes its content, and returns the base64 encoded string along with the file type.

    The file type is determined by the file extension. If the file extension is not
    recognized, 'unknown' will be used as the file type.

    :param file_path: The path to the file to be serialized.
    :return: A tuple containing the base64 encoded string of the file and the file type.
    """
    file_type = get_file_type(file_path)

    # Read the file and encode its contents
    try:
        with open(file_path, "rb") as file:
            file_content = file.read()
            base64_encoded_content = base64.b64encode(file_content).decode("utf-8")
    except Exception as e:
        raise IOError(f"An error occurred while reading the file: {e}")

    return base64_encoded_content, file_type


def get_modified_files(
    start_timestamp: float, end_timestamp: float, source_dir: str, dest_dir: str
) -> List[Dict[str, str]]:
    """Copy files from source_dir that were modified within a specified timestamp range to dest_dir, renaming files if they already exist there. The function excludes files with certain file extensions and names.

    :param start_timestamp: The start timestamp to filter modified files.
    :param end_timestamp: The end timestamp to filter modified files.
    :param source_dir: The directory to search for modified files.
    :param dest_dir: The destination directory to copy modified files to.

    :return: A list of dictionaries with details of file paths in dest_dir that were modified and copied over.
             Dictionary format: {path: "", name: "", extension: ""}
             Files with extensions "__pycache__", "*.pyc", "__init__.py", and "*.cache"
             are ignored.
    """
    modified_files = []
    ignore_extensions = {".pyc", ".cache"}
    ignore_files = {"__pycache__", "__init__.py"}

    for root, dirs, files in os.walk(source_dir):
        # Excluding the directory "__pycache__" if present
        dirs[:] = [d for d in dirs if d not in ignore_files]

        for file in files:
            file_path = os.path.join(root, file)
            file_ext = os.path.splitext(file)[1]
            file_name = os.path.basename(file)

            if file_ext in ignore_extensions or file_name in ignore_files:
                continue

            file_mtime = os.path.getmtime(file_path)
            if start_timestamp < file_mtime < end_timestamp:
                dest_file_path = os.path.join(dest_dir, file)
                copy_idx = 1
                while os.path.exists(dest_file_path):
                    base, extension = os.path.splitext(file)
                    # Handling potential name conflicts by appending a number
                    dest_file_path = os.path.join(dest_dir, f"{base}_{copy_idx}{extension}")
                    copy_idx += 1

                # Copying the modified file to the destination directory
                shutil.copy2(file_path, dest_file_path)

                # Extract user id from the dest_dir and file path
                uid = dest_dir.split("/")[-1]
                relative_file_path = os.path.relpath(dest_file_path, start=dest_dir)
                file_type = get_file_type(dest_file_path)
                file_dict = {
                    "path": f"files/user/{uid}/{relative_file_path}",
                    "name": file_name,
                    "extension": file_ext.replace(".", ""),
                    "type": file_type,
                }
                modified_files.append(file_dict)
    # sort by extension
    modified_files.sort(key=lambda x: x["extension"])
    return modified_files


def init_webserver_folders(root_file_path: str) -> Dict[str, str]:
    """Initialize folders needed for a web server, such as static file directories and user-specific data directories.

    :param root_file_path: The root directory where webserver folders will be created
    :return: A dictionary with the path of each created folder
    """
    files_static_root = os.path.join(root_file_path, "files/")
    static_folder_root = os.path.join(root_file_path, "ui")
    workdir_root = os.path.join(root_file_path, "workdir")
    skills_dir = os.path.join(root_file_path, "skills")
    user_skills_dir = os.path.join(skills_dir, "user")
    global_skills_dir = os.path.join(skills_dir, "global")

    os.makedirs(files_static_root, exist_ok=True)
    os.makedirs(os.path.join(files_static_root, "user"), exist_ok=True)
    os.makedirs(static_folder_root, exist_ok=True)
    os.makedirs(workdir_root, exist_ok=True)
    os.makedirs(skills_dir, exist_ok=True)
    os.makedirs(user_skills_dir, exist_ok=True)
    os.makedirs(global_skills_dir, exist_ok=True)

    folders = {
        "files_static_root": files_static_root,
        "static_folder_root": static_folder_root,
        "workdir_root": workdir_root,
        "skills_dir": skills_dir,
        "user_skills_dir": user_skills_dir,
        "global_skills_dir": global_skills_dir,
    }
    return folders


def delete_files_in_folder(folders: Union[str, List[str]]) -> None:
    """Delete all files and directories in the specified folders.

    :param folders: A list of folders or a single folder string
    """
    if isinstance(folders, str):
        folders = [folders]

    for folder in folders:
        # Check if the folder exists
        if not os.path.isdir(folder):
            print(f"The folder {folder} does not exist.")
            continue

        # List all the entries in the directory
        for entry in os.listdir(folder):
            # Get the full path
            path = os.path.join(folder, entry)
            try:
                if os.path.isfile(path) or os.path.islink(path):
                    # Remove the file or link
                    os.remove(path)
                elif os.path.isdir(path):
                    # Remove the directory and all its content
                    shutil.rmtree(path)
            except Exception as e:
                # Print the error message and skip
                print(f"Failed to delete {path}. Reason: {e}")


def extract_successful_code_blocks(messages: List[Dict[str, str]]) -> List[str]:
    """Parses through a list of messages containing code blocks and execution statuses,.

    returning the array of code blocks that executed successfully and retains
    the backticks for Markdown rendering.

    Parameters:
    messages (List[Dict[str, str]]): A list of message dictionaries containing 'content' and 'role' keys.

    Returns:
    List[str]: A list containing the code blocks that were successfully executed, including backticks.
    """
    successful_code_blocks = []
    # Regex pattern to capture code blocks enclosed in triple backticks.
    code_block_regex = r"```[\s\S]*?```"

    for i, message in enumerate(messages):
        # message = row["message"]
        if message["role"] == "assistant" and message["content"] and "execution succeeded" in message["content"]:  # noqa: SIM102
            if i > 0 and messages[i - 1]["role"] == "user":
                prev_content = messages[i - 1]["content"]
                print("prev_content: ", prev_content)
                # Find all matches for code blocks
                code_blocks = re.findall(code_block_regex, prev_content)
                # Add the code blocks with backticks
                successful_code_blocks.extend(code_blocks)

    return successful_code_blocks


def create_skills_from_code(dest_dir: str, skills: Union[str, List[str]]) -> None:
    """Create skills from a list of code blocks.

    Parameters:
    dest_dir (str): The destination directory to copy all skills to.
    skills (Union[str, List[str]]): A list of strings containing code blocks.
    """
    # Ensure skills is a list
    if isinstance(skills, str):
        skills = [skills]

    # Check if dest_dir exists
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    for skill in skills:
        # Attempt to parse the code and extract the top-level function name
        try:
            parsed = ast.parse(skill)
            function_name = None
            for node in parsed.body:
                if isinstance(node, ast.FunctionDef):
                    function_name = node.name
                    break

            if function_name is None:
                raise ValueError("No top-level function definition found.")

            # Sanitize the function name for use as a file name
            function_name = "".join(ch for ch in function_name if ch.isalnum() or ch == "_")
            skill_file_name = f"{function_name}.py"

        except (ValueError, SyntaxError):
            skill_file_name = "new_skill.py"

        # If the generated/sanitized name already exists, append an index
        skill_file_path = os.path.join(dest_dir, skill_file_name)
        index = 1
        while os.path.exists(skill_file_path):
            base, ext = os.path.splitext(skill_file_name)
            if base.endswith(f"_{index - 1}"):
                base = base.rsplit("_", 1)[0]

            skill_file_path = os.path.join(dest_dir, f"{base}_{index}{ext}")
            index += 1

        # Write the skill to the file
        with open(skill_file_path, "w", encoding="utf-8") as f:
            f.write(skill)


def extract_last_useful_message(messages: List[Dict[str, str]]) -> dict[str, str]:
    """Extract the last useful message from a list of messages.

    Parameters:
    messages (List[Dict[str, str]]): A list of message dictionaries containing 'content' and 'role' keys.

    Returns:
    Dict[str, str]: A dictionary containing the last useful message.
    """
    # reverse order and remove messages with empty content
    messages_reverse_order = [message for message in reversed(messages) if message["content"] != ""]

    last_useful_message = {}
    # messages_reverse_order = messages[::-1]  # reverse the order of the messages list
    for i, message in enumerate(messages_reverse_order):
        if message["role"] == "assistant" and message["content"]:  # noqa: SIM102
            if "execution succeeded" in message["content"]:  # noqa: SIM114
                last_useful_message = messages_reverse_order[i]
                continue
            elif "TERMINATE" in message["content"]:
                previous_message_i = i + 1
                if previous_message_i < len(messages_reverse_order):
                    last_useful_message = messages_reverse_order[previous_message_i]
                continue
    return last_useful_message

def get_or_create_python_eventloop():
    """Get the current event loop or create a new one if there isn't one. Need this hack because of the way the Streamlit works.

    If you get the error "There is no current event loop in thread 'ScriptRunner.scriptThread'" when calling an async function then call this function first.
    Usage:

    ```python
        loop = get_or_create_python_eventloop()
        loop.run_until_complete(async_function())
    ```

    or

    ```python
        get_or_create_python_eventloop()
        await async_function()
    ```

    """
    try:
        import asyncio
    except ImportError:
        logging.warning("Package 'asyncio' not available.")
    try:
        return asyncio.get_event_loop()
    except RuntimeError as ex:
        if "There is no current event loop in thread" in str(ex):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return asyncio.get_event_loop()
