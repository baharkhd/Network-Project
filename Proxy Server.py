import socket
import threading


class ProxyServer:
    forwarding_table = dict()

    def __init__(self):
        addr = ('127.0.0.1', int(input('Please enter the port number:')))

        proxy_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        proxy_server.bind(addr)
        proxy_server.listen()
        self.proxy_server = proxy_server

        self.listen()

    def listen(self):
        while True:
            client, address = self.proxy_server.accept()
            forwarding_port = int(client.recv(1024).decode('ascii'))
            server = self.initiate_connection(forwarding_port)
            self.forwarding_table[address] = (forwarding_port, client, server)

            client_thread = threading.Thread(target=self.client_to_server, args=(server, client, address,))
            client_thread.start()
            server_thread = threading.Thread(target=self.server_to_client, args=(server, client, address,))
            server_thread.start()

    def initiate_connection(self, port):
        socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_.connect(('127.0.0.1', port))
        return socket_

    def client_to_server(self, server, client, address):
        while True:
            try:
                message = client.recv(1024)
                server.send(message)
            except:
                self.forwarding_table[address][1].close()
                self.forwarding_table[address][2].close()

    def server_to_client(self, server, client, address):
        while True:
            try:
                message = server.recv(1024)
                client.send(message)
            except:
                self.forwarding_table[address][2].close()
                self.forwarding_table[address][1].close()


if __name__ == '__main__':
    proxy_s = ProxyServer()
