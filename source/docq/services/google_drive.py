"""Google drive service."""

import logging as log
import os
from typing import Any, Optional, Union

from google.auth.external_account_authorized_user import Credentials as ExtCredentials
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

CREDENTIALS_KEY = "DOCQ_GOOGLE_APPLICATION_CREDENTIALS"
REDIRECT_URL_KEY = "DOCQ_GOOGLE_AUTH_REDIRECT_URL"

GOOGLE_APPLICATION_CREDS_PATH = os.environ.get(CREDENTIALS_KEY)
FLOW_REDIRECT_URI = os.environ.get(REDIRECT_URL_KEY)

SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/userinfo.email',
    'openid'
]

KEY = "google_drive-API"
VALID_CREDENTIALS = "valid_credentials"
INVALID_CREDENTIALS = "invalid_credentials"
AUTH_WRONG_EMAIL = "auth_wrong_email"
AUTH_URL = "auth_url"

CREDENTIALS = Union[Credentials,  ExtCredentials]

def _init() -> None:
    """Initialize."""
    if not GOOGLE_APPLICATION_CREDS_PATH:
        raise Exception("Google application credentials not found.")
    if not os.path.exists(GOOGLE_APPLICATION_CREDS_PATH):
        raise Exception("Google application credentials not found.")
    if not FLOW_REDIRECT_URI:
        raise Exception("Google auth redirect url not found.")


def get_flow() -> InstalledAppFlow:
    """Get Google Drive flow."""
    flow =  InstalledAppFlow.from_client_secrets_file(
        GOOGLE_APPLICATION_CREDS_PATH, SCOPES
    )
    flow.redirect_uri = FLOW_REDIRECT_URI
    return flow


def get_credentials(creds: dict) -> CREDENTIALS:
    """Get credentials from user info."""
    _creds =  Credentials.from_authorized_user_info(creds, SCOPES)
    if _creds.expired and _creds.refresh_token:
        _creds.refresh(Request())
    return _creds


def refresh_credentials(creds: CREDENTIALS) -> CREDENTIALS:
    """Refresh credentials."""
    creds.refresh(Request())
    return creds


def get_gdrive_authorized_email(creds: CREDENTIALS) -> str:
    """Get user email."""
    service = build('oauth2', 'v2', credentials=creds)
    return service.userinfo().get().execute()['email']


def get_auth_url_params(email: Optional[str] = None) -> dict:
    """Get authorization url params."""
    authorization_params = {
        "access_type": "offline",
        "prompt": "consent",
    }
    if email:
        authorization_params["login_hint"] = email
    return authorization_params


def list_folders(creds: dict) -> list[dict]:
    """List folders."""
    _creds = get_credentials(creds)
    drive = build('drive', 'v3', credentials=_creds)
    folders = drive.files().list(
        q="mimeType='application/vnd.google-apps.folder'",
        fields="files(id, name, parents, mimeType, modifiedTime)",
    ).execute()
    return folders.get('files', [])


def get_drive_service(creds: dict) -> Any:  # noqa: ANN401
    """Get drive service."""
    _creds = get_credentials(creds)
    return build('drive', 'v3', credentials=_creds)


def download_file(service: Any, file_id: str, file_name: str) -> None:
    """Download file."""
    request = service.files().get_media(fileId=file_id)
    with open(file_name, "wb") as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            log.debug("Download - %s: %d%", file_name, int(status.progress() * 100))
