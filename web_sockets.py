#!python
from kiteconnect import WebSocket

# Initialise.
kws = WebSocket("your_api_key", "your_public_token", "logged_in_user_id")


# Callback for tick reception.
def on_tick(tick, ws):
    print(tick)


# Callback for successful connection.
def on_connect(ws):
    # Subscribe to a list of instrument_tokens (RELIANCE and ACC here).
    ws.subscribe([738561, 5633])

    # Set RELIANCE to tick in `full` mode.
    ws.set_mode(ws.MODE_FULL, [738561])


# Assign the callbacks.
kws.on_tick = on_tick
kws.on_connect = on_connect

# To enable auto reconnect WebSocket connection in case of network failure
# - First param is interval between reconnection attempts in seconds.
# Callback `on_reconnect` is triggered on every reconnection attempt. (Default interval is 5 seconds)
# - Second param is maximum number of retries before the program exits triggering `on_noreconnect` calback. (Defaults to 50 attempts)
# Note that you can also enable auto reconnection        while initialising websocket.
# Example `kws = WebSocket("your_api_key", "your_public_token", "logged_in_user_id", reconnect=True, reconnect_interval=5, reconnect_tries=50)`
kws.enable_reconnect(reconnect_interval=5, reconnect_tries=50)

# Infinite loop on the main thread. Nothing after this will run.
# You have to use the pre-defined callbacks to manage subscriptions.
kws.connect()