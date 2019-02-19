import time

from channels.generic.websocket import WebsocketConsumer
import json


class ZWSSimulator(WebsocketConsumer):
    def connect(self):
        print('Connected')
        self.accept()

    def disconnect(self, close_code):
        print('Disconnected')

    def receive(self, text_data):
        print('Receiving text: ' + text_data)
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        self.send(text_data=json.dumps({
            'message': message
        }))

    def send(self, text_data=None, bytes_data=None, close=False):
        """
        Sends a reply back down the WebSocket
        """
        counter = 0
        while True:
            super().send(json.dumps({"type": "websocket.send", "text": "Hola " + str(counter)}))
            counter += 1
            time.sleep(1)
