"""Microsoft OneDrive Service Module."""
import json
import logging as log
import os
from datetime import datetime
from typing import Optional, Self

from microsoftgraph.client import Client

DOCQ_MS_ONEDRIVE_CLIENT_ID_KEY = "DOCQ_MS_ONEDRIVE_CLIENT_ID"
DOCQ_MS_ONEDRIVE_CLIENT_SEC_RET_KEY = "DOCQ_MS_ONEDRIVE_CLIENT_SECRET"
DOCQ_MS_ONEDRIVE_REDIRECT_URI_KEY = "DOCQ_MS_ONEDRIVE_REDIRECT_URI"

SCOPES = [
    "offline_access",
    "User.Read",
    "Files.Read",
]


class Credential:
    """Microsoft OneDrive Credential."""

    __token = {}
    __created_at = 0

    def __init__(self: Self, token: dict) -> None:
        """Initialize the credential."""
        self.__token = token
        self.__created_at = int(datetime.now().timestamp())

    @property
    def to_json(self: Self) -> str:
        """Get the token as json."""
        if self.expired:
            self.token = refresh_token(self.token)
        return json.dumps(self.token)

    @property
    def token(self: Self) -> dict:
        """Get the token."""
        return self.__token

    @token.setter
    def token(self: Self, token: dict) -> None:
        """Set the token."""
        self.__token = token
        self.__created_at = int(datetime.now().timestamp())

    @property
    def expired(self: Self) -> bool:
        """Token expired status."""
        return int(datetime.now().timestamp()) > self.__created_at + int(self.token.get("expires_in", 0))


def get_client(credential: Optional[Credential] = None) -> Client:
    """Get the Microsoft OneDrive client."""
    client_id = os.environ.get(DOCQ_MS_ONEDRIVE_CLIENT_ID_KEY, "")
    client_secret = os.environ.get(DOCQ_MS_ONEDRIVE_CLIENT_SEC_RET_KEY, "")
    client = Client(client_id, client_secret)
    if credential is not None:
        if credential.expired:
            credential.token = refresh_token(credential.token)
        client.set_token(credential.token)
    return client


def get_auth_url(data: dict) -> Optional[dict]:
    """Get the auth url for Microsoft OneDrive."""
    try:
        redirect_uri = os.environ.get(DOCQ_MS_ONEDRIVE_REDIRECT_URI_KEY, "")
        client = get_client()
        code = data.get("code", None)
        if code is not None:
            response = client.exchange_code(redirect_uri, code)
            log.info("services.ms_onedrive -- get_auth_url -- Response: %s", response.data)
            return {"credential": Credential(response.data)}
        else:
            state = data.get("state", None)
            return {"auth_url": client.authorization_url(redirect_uri, SCOPES, state)}
    except Exception as e:
        log.error("services.ms_onedrive -- get_auth_url -- Error: %s", e)


def refresh_token(token: dict) -> dict:
    """Refresh the Microsoft OneDrive token."""
    client = get_client()
    redirect_uri = os.environ.get(DOCQ_MS_ONEDRIVE_REDIRECT_URI_KEY, "")
    response = client.refresh_token(token["refresh_token"], redirect_uri)
    return response.data


def validate_credentials(credential: Credential) -> Credential:
    """Validate the Microsoft OneDrive credentials."""
    if credential.expired:
        credential.token = refresh_token(credential.token)
    return credential


def list_folders(credential: Credential) -> list[dict]:
    """List the root folders in Microsoft OneDrive."""
    try:
        client = get_client(credential)
        response = client.files.drive_root_children_items({
            "$select": "id,name,folder",
            "$filter": "folder ne null and folder/childCount gt 0",
            "$top": 1000,
        })
        return response.data.get("value", [])
    except Exception as e:
        log.error("services.ms_onedrive -- list_folders -- Error: %s", e)
        return []


def download_file(client: Client, file_id: str, file_path: str) -> None:
    """Download a file from Microsoft OneDrive."""
    try:
        with open(file_path, "wb") as file:
            data = client.files.drive_download_contents(file_id).data
            file.write(data)
    except Exception as e:
        log.error("services.ms_onedrive -- download_file -- Error: %s", e)


def api_enabled() -> bool:
    """Check if the Microsoft OneDrive API is enabled."""
    return (
        os.environ.get(DOCQ_MS_ONEDRIVE_CLIENT_ID_KEY) is not None
        and os.environ.get(DOCQ_MS_ONEDRIVE_CLIENT_SEC_RET_KEY) is not None
        and os.environ.get(DOCQ_MS_ONEDRIVE_REDIRECT_URI_KEY) is not None
    )


def _init() -> None:
    """Initialize the Microsoft OneDrive service."""
    if api_enabled():
        log.info("Microsoft OneDrive API enabled.")
    else:
        log.info("Microsoft OneDrive API disabled.")
