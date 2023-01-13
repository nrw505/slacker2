from slack_sdk.socket_mode.client import BaseSocketModeClient
from slack_sdk.socket_mode.response import SocketModeResponse
from slack_sdk.socket_mode.request import SocketModeRequest


def logging_listener(client: BaseSocketModeClient, request: SocketModeRequest) -> None:
    print(f"{__name__} - request.type: {request.type}")
    print(f"{__name__} - request.payload: {request.payload}")
