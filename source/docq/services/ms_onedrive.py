"""Microsoft OneDrive Service Module."""
import logging as log
import os
from datetime import datetime, timedelta
from typing import Optional

from microsoftgraph.client import Client

DOCQ_MS_ONEDRIVE_CLIENT_ID_KEY = "DOCQ_MS_ONEDRIVE_CLIENT_ID"
DOCQ_MS_ONEDRIVE_CLIENT_SEC_RET_KEY = "DOCQ_MS_ONEDRIVE_CLIENT_SECRET"
DOCQ_MS_ONEDRIVE_REDIRECT_URI_KEY = "DOCQ_MS_ONEDRIVE_REDIRECT_URI"

SCOPES = [
    "offline_access",
    "User.Read",
    "Files.Read",
]


def _token_expired(token: dict) -> bool:
    """Check if the token is expired."""
    return datetime.now() > datetime.fromtimestamp(token["expiry"])


def _remove_token_expiry(token: dict) -> dict:
    """Remove the token expiry."""
    _token = token.copy()
    _token.pop("expiry", None)
    return _token


def _set_token_expiry(token: dict) -> dict:
    """Set the token expiry."""
    expiry = datetime.now() + timedelta(seconds=token["expires_in"])
    token["expiry"] = expiry.timestamp()
    return token


def get_client(token: Optional[dict] = None) -> Client:
    """Get the Microsoft OneDrive client."""
    client_id = os.environ.get(DOCQ_MS_ONEDRIVE_CLIENT_ID_KEY, "")
    client_secret = os.environ.get(DOCQ_MS_ONEDRIVE_CLIENT_SEC_RET_KEY, "")
    client = Client(client_id, client_secret)
    if token is not None:
        log.info("services.ms_onedrive -- get_client -- Token: %s", token)
        if _token_expired(token):
            token = refresh_token(token)
        client.set_token(_remove_token_expiry(token))
    return client


def get_auth_url(data: dict) -> Optional[dict]:
    """Get the auth url for Microsoft OneDrive."""
    try:
        redirect_uri = os.environ.get(DOCQ_MS_ONEDRIVE_REDIRECT_URI_KEY, "")
        client = get_client()
        code = data.get("code", None)
        if code is not None:
            response = client.exchange_code(redirect_uri, code)
            token =  _set_token_expiry(response.data)
            log.info("services.ms_onedrive -- get_auth_url -- Response: %s", token)
            return {"credential": token}
        else:
            state = data.get("state", None)
            return {"auth_url": client.authorization_url(redirect_uri, SCOPES, state)}
    except Exception as e:
        log.error("services.ms_onedrive -- get_auth_url -- Error: %s", e)


def refresh_token(token: dict) -> dict:
    """Refresh the Microsoft OneDrive token."""
    client = get_client()
    redirect_uri = os.environ.get(DOCQ_MS_ONEDRIVE_REDIRECT_URI_KEY, "")
    response = client.refresh_token(redirect_uri=redirect_uri, refresh_token=token["refresh_token"])
    token = _set_token_expiry(response.data)
    log.info("services.ms_onedrive -- refresh_token -- Token expiry: %s", token["expiry"])
    return token


def validate_credentials(token: dict) -> dict:
    """Validate the Microsoft OneDrive credentials."""
    if _token_expired(token):
        token = refresh_token(token)
    return token


def list_folders(token: dict) -> list[dict]:
    """List the root folders in Microsoft OneDrive."""
    try:
        client = get_client(token)
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
