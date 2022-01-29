import socket
import threading

addr = ('127.0.0.1', 5050)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(addr)
server.listen()


def handle(client):
    # initiate connection via login or signup, then a while loop to handle client queries.
    pass


while True:
    client, address = server.accept()
    print(address)

    client_thread = threading.Thread(target=handle, args=(client, ))
    client_thread.start()
