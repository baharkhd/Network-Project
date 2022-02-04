import socket
import threading
from commons import CHAT_SERVER_PORT


class ChatServer:
    users = []

    def __init__(self):
        addr = ('127.0.0.1', CHAT_SERVER_PORT)

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(addr)
        server.listen()

        self.server = server

        self.listen()

    def listen(self):
        while True:
            print("Listening For a Client...")
            client, address = self.server.accept()
            print("client arrived! ", address)

            client_thread = threading.Thread(target=self.handle, args=(client,))
            client_thread.start()

    def main_menu(self, client):
        msg = '1. Sign Up\n2. Login\n3. Exit\n'
        client.send(msg.encode('ascii'))

    def handle(self, client):
        # initiate connection via login or signup, then a while loop to handle client queries.
        self.main_menu(client)
        message = client.recv(4096).decode('ascii').strip()
        print("* message received from client: ", message)
        if message == '1':
            self.sign_up(client)
        elif message == '2':
            self.login(client)
            pass
        elif message == '3':
            #TODO exit
            pass
        else:
            #TODO wrong inp
            pass

    def sign_up(self, client):
        msg = 'Please enter your username.'
        client.send(msg.encode('ascii'))
        while True:
            username = client.recv(4096).decode('ascii')
            for user in self.users:
                if user.username == username:
                    msg = 'This username is already existed or invalid. Please enter another one.'
                    client.send(msg.encode('ascii'))
                    break
            else:
                if username == '0':
                    msg = 'This username is already existed or invalid. Please enter another one.'
                    client.send(msg.encode('ascii'))
                else:
                    client.username = username
                    break
        msg = 'Please enter your password.'
        client.send(msg.encode('ascii'))
        password = client.recv(4096).decode('ascii')
        client.password = password

        # for user in self.users:
        #     client.messages[user] = []
        #     client.unreadMsgNum[user] = []
        self.users.append(client)
        self.main_menu(client)

    def login(self, client):
        msg = 'Please enter your username.'
        client.send(msg.encode('ascii'))
        username = client.recv(4096).decode('ascii')
        msg = 'Please enter your password.'
        client.send(msg.encode('ascii'))
        password = client.recv(4096).decode('ascii')

        if client.username == username and client.password == password:
            self.show_users(client)
        else:
            msg = 'Incorrect username or password.'
            client.send(msg.encode('ascii'))
            self.main_menu(client)

    def show_users(self, client):
        pass