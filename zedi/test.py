from websocket import create_connection

ws = create_connection("ws://localhost:8000/ws/chat/")
print("Sending 'Hello, World'...")
ws.send('{"message": "mola"}')
print("Sent")
print("Reeiving...")
result = ws.recv()
print("Received '%s'" % result)
ws.close()
