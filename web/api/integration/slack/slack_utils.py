"""Slack application utils for Docq."""
from os import environ
from typing import Union

from slack_sdk import WebClient

BOT_TOKEN = environ.get("SLACK_BOT_TOKEN")

def get_slack_client() -> WebClient:
    """Get a Slack client."""
    return WebClient(token=BOT_TOKEN)

def get_slack_user_id( email: str ) -> str:
    """Get a Slack user ID."""
    client = get_slack_client()
    response = client.users_lookupByEmail(email=email)
    return response["user"]["id"]

def get_slack_user_email( user_id: str ) -> str:
    """Get a Slack user email."""
    client = get_slack_client()
    response = client.users_info(user=user_id)
    return response["user"]["profile"]["email"]

def get_slack_user_name( user_id: str ) -> str:
    """Get a Slack user name."""
    client = get_slack_client()
    response = client.users_info(user=user_id)
    return response["user"]["name"]

def get_slack_user_info( user_id: str ) -> dict:
    """Get a Slack user info."""
    client = get_slack_client()
    response = client.users_info(user=user_id)
    return response["user"]

def get_slack_channel_id( channel_name: str ) -> str:
    """Get a Slack channel ID."""
    client = get_slack_client()
    response = client.conversations_list()
    for channel in response["channels"]:
        if channel["name"] == channel_name:
            return channel["id"]
    return ""

def get_slack_channel_name( channel_id: str ) -> str:
    """Get a Slack channel name."""
    client = get_slack_client()
    response = client.conversations_info(channel=channel_id)
    return response["channel"]["name"]

def get_slack_channel_info( channel_id: str ) -> dict:
    """Get a Slack channel info."""
    client = get_slack_client()
    response = client.conversations_info(channel=channel_id)
    return response["channel"]

def list_slack_channels() -> list[dict[str, Union[str, dict[str, str]]]]:
    """List Slack channels."""
    client = get_slack_client()
    response = client.conversations_list(types="public_channel,private_channel")
    return [ channel for channel in response["channels"] if  channel["is_member"] ]

def list_team_channels( team_id: str ) -> list[dict[str, Union[str, dict[str, str]]]]:
    """List team channels."""
    client = get_slack_client()
    response = client.conversations_list(types="public_channel,private_channel", team_id=team_id)
    return [ channel for channel in response["channels"] ]
