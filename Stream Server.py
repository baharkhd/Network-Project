import socket
import threading

addr = ('127.0.0.1', 5060)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(addr)
server.listen()


def send_vid(client, vid_name):
    # Todo
    pass


def handle(client):
    # Don't forget to include stop-stream feature in your code.
    # To send the video, You can create a new thread with function send_vid and look for incoming messages from client.
    pass


while True:
    client, address = server.accept()
    print(address)

    client_thread = threading.Thread(target=handle, args=(client, ))
    client_thread.start()
