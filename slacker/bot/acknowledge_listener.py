from slack_sdk.socket_mode.client import BaseSocketModeClient
from slack_sdk.socket_mode.response import SocketModeResponse
from slack_sdk.socket_mode.request import SocketModeRequest


def acknowledge_listener(
    client: BaseSocketModeClient, request: SocketModeRequest
) -> None:
    # Acknowledge every event we receive
    response = SocketModeResponse(envelope_id=request.envelope_id)
    client.send_socket_mode_response(response)
