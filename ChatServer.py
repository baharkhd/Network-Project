import re
import socket
import threading
from commons import CHAT_SERVER_PORT
import time
from datetime import datetime

from Message import Message
from User import User


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

    def handle(self, client):
        state = 0
        # initiate connection via login or signup, then a while loop to handle client queries.
        # self.main_menu(client)
        while True:
            if state == 0:
                state, user = self.handle_main_menu(client, state)
            elif state == 1:
                state, username = self.handle_mailbox(client, state, user)
            else:
                state = self.handle_chat(client, state, user, username)

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
                return 1, user
                # break
        else:
            client.send('Incorrect username or password.'.encode('ascii'))
            return 0, None

    def handle_main_menu(self, client, state):
        message = client.recv(4096).decode('ascii').strip()
        print("* message received from client: ", message)
        user = None
        if message == '1':
            self.sign_up(client)
        elif message == '2':
            state, user = self.login(client)
        elif message == '3':
            pass
            # TODO exit
        else:
            msg = 'The command must be an integer from 1 to 3. lalalalalala'
            client.send(msg.encode('ascii'))
        return state, user

    def handle_mailbox(self, client, state, user: User):
        last_message = []
        username = None
        for u in self.users:
            if u != user:
                print(f'Check for error: {u.username}')
                if u not in user.messages:
                    m = Message(msg='', date=datetime(2000, 1, 1), sender=user, receiver=u)
                    user.messages[u] = [m]
                    u.messages[user] = [m]
                    user.unreadMsgNum[u] = 0
                    u.unreadMsgNum[user] = 0
                last_message.append(
                    {'username': u.username, 'date': u.messages[user][-1].date, 'unread': user.unreadMsgNum[u]})
        last_message = sorted(last_message, key=lambda i: i['date'], reverse=True)
        user_count = len(last_message)
        client.send(str(user_count).encode('ascii'))
        print(last_message)
        for u in last_message:
            msg = u['username'] + ' ' + str(u['unread'])
            client.send(msg.encode('ascii'))
            time.sleep(0.1)

        message = client.recv(4096).decode('ascii').strip()
        if message == '0':
            state = 0
        else:
            for u in self.users:
                if u.username == message:
                    username = u
                    state = 2
        return state, username

    def handle_chat(self, client, state, user1: User, user2: User):
        self.load_x(5, client, user1, user2)
        message = client.recv(4096).decode('ascii').strip()
        if message[0] == '\\':
            if re.search('^load_\d+$', message[1:0]):
                message_arr = message.split('_')
                self.load_x(int(message_arr[1]), client, user1, user2)
            elif message[1:] == 'exit':
                state = 1
            else:
                m = Message(message, datetime.now(), user1, user2)
                user1.messages[user2].append(m)
                user2.messages[user1].append(m)
        return state

    def load_x(self, k, client, user1: User, user2: User):
        messages_count = len(user1.messages[user2]) - 1  # one msg is additional (initial msg)
        if messages_count < k:
            k = messages_count
        client.send(str(k).encode('ascii'))
        last_x_messages = user1.messages[user2][-k:-1] + [user1.messages[user2][-1]]
        for m in last_x_messages:
            msg = m.sender + ' ' + m.msg
            client.send(msg.encode('ascii'))
            time.sleep(0.1)



if __name__ == "__main__":
    stream_server = ChatServer()