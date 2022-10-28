from time import sleep
import http_server
import websocket_server
websocket_server.run()
http_server.run()

while True:
    sleep(100)