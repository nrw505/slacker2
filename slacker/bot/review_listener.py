from slack_sdk.socket_mode.client import BaseSocketModeClient
from slack_sdk.socket_mode.response import SocketModeResponse
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.listeners import SocketModeRequestListener


def verify_github_pr_url(url):
    return False


def review_listener(client: BaseSocketModeClient, request: SocketModeRequest) -> None:
    # Is it for me?
    if (
        request.type == "interactive"
        and request.payload.get("type") == "shortcut"
        and request.payload["callback_id"] == "review"
    ):
        # Acknowledge the event
        response = SocketModeResponse(envelope_id=request.envelope_id)
        client.send_socket_mode_response(response)

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
                        "block_id": "pr",
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
        # Check the payload for errors
        response_payload = None
        pr_url = request.payload["view"]["state"]["values"]["pr"]["pr_url"]["value"]

        print(f"PR URL: {pr_url}")
        if not verify_github_pr_url(pr_url):
            response_payload = {
                "response_action": "errors",
                "errors": {
                    "pr": "That is not a GitHub PR URL",
                },
            }

        # Send the acknowledgement, possibly with errors
        print(f"response: {response_payload}")
        response = SocketModeResponse(
            envelope_id=request.envelope_id, payload=response_payload
        )
        client.send_socket_mode_response(response)
