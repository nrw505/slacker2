from slack_sdk.socket_mode.client import BaseSocketModeClient
from slack_sdk.socket_mode.response import SocketModeResponse
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.listeners import SocketModeRequestListener


def review_listener(client: BaseSocketModeClient, request: SocketModeRequest) -> None:
    # Is it for me?
    if (
        request.type == "interactive"
        and request.payload.get("type") == "shortcut"
        and request.payload["callback_id"] == "review"
    ):
        # respond to /slacker review
        client.web_client.views_open(
            trigger_id=request.payload["trigger_id"],
            view={
                "type": "modal",
                "callback_id": "review-modal",
                "title": {"type": "plain_text", "text": "Request a PR review"},
                "submit": {"type": "plain_text", "text": "Go!"},
                "blocks": [
                    {
                        "type": "input",
                        "label": {
                            "type": "plain_text",
                            "text": "PR's :github: GitHub URL",
                            "emoji": True,
                        },
                        "element": {
                            "type": "url_text_input",
                            "action_id": "pr_url",
                            "focus_on_load": True,
                        },
                    },
                ],
            },
        )

    if (
        request.type == "interactive"
        and request.payload.get("type") == "view_submission"
        and request.payload["view"]["callback_id"] == "review-modal"
    ):
        # Handle the review modal submission
        pass
