import socket
import threading
from datetime import datetime

import Message
from User import User


class ChatServer:
    users = []

    def __init__(self):
        addr = ('127.0.0.1', 5050)

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

    def handle(self, client):
        state = 0
        # initiate connection via login or signup, then a while loop to handle client queries.
        # self.main_menu(client)
        while True:
            if state == 0:
                state = self.handle_main_menu(client, state)
            elif state == 1:
                state = self.handle_mailbox(client, state)

    def sign_up(self, client):
        while True:
            username = client.recv(4096).decode('ascii')
            if username != '0':
                for user in self.users:
                    if user.username == username:
                        client.send(
                            'This username is already existed or invalid. Please enter another one.'.encode('ascii'))
                        break
                else:
                    client.send('Please enter your password.'.encode('ascii'))
                    password = client.recv(4096).decode('ascii')
                    user = User()
                    user.username = username
                    user.password = password
                    self.users.append(user)
                    print(f'{username} registered')
                    break

    def login(self, client):
        username = client.recv(4096).decode('ascii')
        password = client.recv(4096).decode('ascii')
        for user in self.users:
            if user.username == username and user.password == password:
                client.send('Logged in successfully.'.encode('ascii'))
                return 1
                # break
        else:
            client.send('Incorrect username or password.'.encode('ascii'))
            return 0

    def show_users(self, client):
        all_users = self.users
        for user in all_users:
            if user not in client.messages:
                chat_initial = Message('', datetime(2000, 1, 1))
                client.messages[user] = []
                user.messages[client] = []
                client.unreadMsgNum[user] = 0
                user.unreadMsgNum[client] = 0

    def handle_main_menu(self, client, state):
        message = client.recv(4096).decode('ascii').strip()
        print("* message received from client: ", message)
        if message == '1':
            self.sign_up(client)
        elif message == '2':
            state = self.login(client)
        elif message == '3':
            pass
            # TODO exit
        else:
            msg = 'The command must be an integer from 1 to 3. lalalalalala'
            client.send(msg.encode('ascii'))
        return state

    def handle_mailbox(self, client, state):
        message = client.recv(4096).decode('ascii').strip()
        if message == 'Q':
            state = 0
        return state


if __name__ == "__main__":
    stream_server = ChatServer()
