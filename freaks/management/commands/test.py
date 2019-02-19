import json

from django.core.management.base import BaseCommand

# from helpers import ZerodhaWS
import websocket
import _thread as thread
import time


class Command(BaseCommand):
    help = 'Sync instruments from Zerodha'

    def handle(self, *args, **kwargs):
        ZerodhaWS.connect()


def on_message(ws, message):
    print(message)


def on_error(ws, error):
    print(error)


def on_close(ws):
    print("### closed ###")


def on_open(ws):
    def run(*args):
        data = {"message": "voila"}
        ws.send(json.dumps(data))

    thread.start_new_thread(run, ())


if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("ws://localhost:9001/ws/chat/",
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.on_open = on_open
    ws.run_forever()
