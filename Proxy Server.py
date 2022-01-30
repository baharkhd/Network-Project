import socket
import threading

addr = ('127.0.0.1', int(input('Please enter the port number:')))

proxy_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
proxy_server.bind(addr)
proxy_server.listen()

forwarding_table = dict()


def initiate_connection(port):
    socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_.connect(('127.0.0.1', port))
    return socket_


def client_to_server(server, client, address):
    while forwarding_table[address][3]:
        try:
            message = client.recv(1024)
            if message.decode('ascii') == '/ProxyExit':
                forwarding_table[address][3] = False
            else:
                server.send(message)
        except:
            forwarding_table[address][3] = False
    client.close()


def server_to_client(server, client, address):
    while forwarding_table[address][3]:
        try:
            message = server.recv(1024)
            client.send(message)
        except:
            forwarding_table[address][3] = False
    server.close()


while True:
    client, address = proxy_server.accept()
    forwarding_port = int(client.recv(1024).decode('ascii'))
    server = initiate_connection(forwarding_port)
    forwarding_table[address] = (forwarding_port, client, server, True)

    client_thread = threading.Thread(target=client_to_server, args=(server, client, address, ))
    client_thread.start()
    server_thread = threading.Thread(target=server_to_client, args=(server, client, address, ))
    server_thread.start()
