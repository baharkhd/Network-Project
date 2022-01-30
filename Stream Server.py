import socket
import threading


class StreamServer:

    def __init__(self):
        addr = ('127.0.0.1', 5060)

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(addr)
        server.listen()

        self.server = server
        self.listen()

    def listen(self):
        while True:
            client, address = self.server.accept()
            print(address)

            client_thread = threading.Thread(target=self.handle, args=(client,))
            client_thread.start()

    def send_vid(self, client, vid_name):
        # Todo
        pass

    def handle(self, client):
        # Don't forget to include stop-stream feature in your code.
        # To send the video, You can create a new thread with function send_vid and look for incoming messages from client.
        pass


if __name__ == "__main__":
    stream_server = StreamServer()
