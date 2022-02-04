import re
import socket
import threading
import time
from datetime import datetime

from Message import Message
from User import User
from commons import CHAT_SERVER_PORT
from commons import SEPARATOR


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
                    user.messages = {}
                    user.unreadMsgNum = {}

                    self.users.append(user)
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
        last_messages = []
        username = None
        for u in self.users:
            if u.username != user.username:
                if not u.username in user.messages.keys():
                    u.messages[user.username] = [Message(msg='', date=datetime(2000, 1, 1), sender=user, receiver=u)]

                    user.messages[u.username] = [Message(msg='', date=datetime(2000, 1, 1), sender=user, receiver=u)]
                    user.unreadMsgNum[u.username] = 0
                    u.unreadMsgNum[user.username] = 0

                last_messages.append(
                    {'username': u.username, 'date': u.messages[user.username][-1].date,
                     'unread': user.unreadMsgNum[u.username],
                     'msg': u.messages[user.username][-1].msg})

        last_messages = sorted(last_messages, key=lambda i: i['date'], reverse=True)

        print(last_messages)
        users_messages = []
        for u in last_messages:
            msg = u['username'] + ' ' + str(u['unread'])
            users_messages.append(msg)
            # client.send(msg.encode('ascii'))
            # time.sleep(0.1)

        mailbox_message = SEPARATOR.join(users_messages)
        client.send(mailbox_message.encode('ascii'))

        message = client.recv(4096).decode('ascii').strip()
        if message == '0':
            state = 0
        else:
            for u in self.users:
                if u.username == message:
                    username = u.username
                    state = 2
                    user.unreadMsgNum[u.username] = 0
                    break
        return state, username

    def handle_chat(self, client, state, user1: User, user2: User):
        self.load_x(5, client, user1, user2)
        # message_receiving_thread = threading.Thread(target=self.receive_msg, args=(client, state, user1, user2))
        # message_receiving_thread.start()
        while True:
            message = client.recv(4096).decode('ascii').strip()
            time.sleep(0.1)
            if message[0] == '/':
                if re.search('^load_\d+$', message[1:]):
                    message_arr = message.split('_')
                    self.load_x(int(message_arr[1]), client, user1, user2)
                elif message[1:] == 'exit':
                    state = 1
                    break
            else:
                m = Message(message, datetime.now(), user1, user2)
                user1.messages[user2.username].append(m)
                user2.messages[user1.username].append(m)
                # print(f'message sent from {user1.username} to {user2.username}')
                # for u in self.users:
                #     print(f'{u.username}')
                #     for i in u.messages[user1.username]:
                #         print(i.msg)
                user2.unreadMsgNum[user1.username] += 1
                user1.unreadMsgNum[user2.username] = 0

        return state

    def load_x(self, k, client, user1: User, user2: User):
        messages_count = len(user1.messages[user2.username]) - 1  # one msg is additional (initial msg)
        if messages_count < k:
            k = messages_count
        client.send(str(k).encode('ascii'))
        time.sleep(0.1)
        if k == 0:
            return
        last_x_messages = user1.messages[user2.username][-k:]
        for m in last_x_messages:
            msg = m.sender.username + ' ' + m.msg
            client.send(msg.encode('ascii'))
            time.sleep(0.1)

    def receive_msg(self, client, state, user1: User, user2: User):
        while True:
            if state != 2:
                break
            if user1.unreadMsgNum[user2.username]:
                client.send(str(user1.unreadMsgNum[user2.username]).encode('ascii'))
                time.sleep(0.1)
                new_messages = user1.messages[user2.username][-user1.unreadMsgNum[user2.username]:]
                for m in new_messages:
                    user1.unreadMsgNum[user2.username] -= 1
                    msg = m.sender.username + ' ' + m.msg
                    client.send(msg.encode('ascii'))
                    time.sleep(0.1)


if __name__ == "__main__":
    stream_server = ChatServer()
