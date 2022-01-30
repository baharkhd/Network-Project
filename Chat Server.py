import socket
import threading

class ChatServer:

    def __init__(self):
        addr = ('127.0.0.1', 5050)

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(addr)
        server.listen()

        self.server = server

        self.listen()

    def listen(self):
        while True:
            client, address = self.server.accept()
            print(address)

            client_thread = threading.Thread(target=handle, args=(client, ))
            client_thread.start()



    def handle(self, client):
        # initiate connection via login or signup, then a while loop to handle client queries.
        pass

