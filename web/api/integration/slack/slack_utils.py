"""Slack application utils."""
from docq.integrations import manage_slack
from opentelemetry import trace
from slack_sdk import WebClient

tracer = trace.get_tracer(__name__)



def get_org_id(team_id: str) -> int | None:
    """Get the org id for a Slack team / workspace."""
    result = manage_slack.list_docq_slack_installations(org_id=None, team_id=team_id)
    return result[0].org_id if result else None


@tracer.start_as_current_span(name="list_slack_team_channels")
def list_slack_team_channels(app_id: str, team_id: str) -> list[dict[str, str]]:
    """List Slack team channels."""
    token = manage_slack.get_slack_bot_token(app_id, team_id)
    client = WebClient(token=token)
    response = client.conversations_list(
        team_id=team_id, exclude_archived=True, types="public_channel, private_channel"
    )

    return [channel for channel in response["channels"] if channel["is_member"]]
