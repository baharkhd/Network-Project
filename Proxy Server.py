import socket
import threading

addr = ('127.0.0.1', int(input('Please enter the port number:')))

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(addr)
server.listen()


def initiate_connection(client):
    pass


def handle(client):
    pass


while True:
    client, address = server.accept()
    print(address)

    client_thread = threading.Thread(target=handle, args=(client, ))
    client_thread.start()
