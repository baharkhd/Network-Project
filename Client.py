import pickle
import queue
import re
import socket
import struct
import threading
import time
from enum import Enum
# import pyaudio
from enum import Enum
import traceback

import cv2
import cv2
from commons import SEPARATOR
from User import User
from commons import STREAM_SERVER_PORT, CHAT_SERVER_PORT

number_pattern = re.compile("^[0-9]+$")

VIDEO_SOCKET = 'VIDEO_SOCKET'
AUDIO_SOCKET = "AUDIO_SOCKET"


class FirewallType(Enum):
    blacklist = 0
    whitelist = 1


class State(Enum):
    main_menu = 0
    admin = 1
    user = 2
    chat = 3
    stream = 4


class VideoRequestState(Enum):
    not_started = 0
    pending_for_list = 1  # has sent request, but not received list of videos yet
    received = 2
    pending_for_video = 3
    idle = 4
    after_ending_stream = 5


class ChatStates(Enum):
    login_signup_menu = 0
    mailbox = 1
    chat = 2


class Client(User):
    ports = []
    firewall_type = FirewallType.blacklist
    proxy = None
    state = State.main_menu

    video_request_state = VideoRequestState.not_started
    chat_state = ChatStates.login_signup_menu
    videos_num = 0

    stop_video = False

    def __init__(self):
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.video_stream_socket = None
        self.audio_stream_socket = None
        self.start_client()

    def start_client(self):
        password = input('Please enter a password, this will be used for further changes'
                         ' in the firewall of the system.\n')
        self.admin_password = password

        count = 0
        while True:
            try:
                if self.state == State.main_menu:
                    print('1. Connect to external servers.\n2. Login as admin.\n3. Exit.')
                    try:
                        inp = int(input())
                        if inp > 3 or inp < 1:
                            print('The command must be an integer from 1 to 3.')
                            continue
                        if inp == 1:
                            self.state = State.user
                        elif inp == 2:
                            self.state = State.admin
                        else:
                            break
                    except:
                        print('The command must be an integer from 1 to 3.')

                elif self.state == State.admin:
                    print('Please enter your password:')
                    inp = input()
                    while inp != self.admin_password:
                        print('Incorrect password. Try again ot type /exit to exit to main menu.')
                        inp = input()
                        if inp == '/exit':
                            self.state = State.main_menu
                            continue
                    print('''
                    You are now in admin mode.
                    You can use 
                        activate blacklist firewall
                        activate whitelist firewall
                    to change firewall mode.
                    You can also use
                        open port <num>
                        close port <num>
                        check port <num>
                    to open, close, or check a port.
                    "/exit" command will bring you to main menu.
                    ''')
                    while True:
                        inp = input()
                        if inp == '/exit':
                            self.state = State.main_menu
                            break
                        self.firewall_change(inp)
                elif self.state == State.user:
                    self.proxy = None
                    print('1. Chat\n2. Stream')
                    self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    inp = input()
                    inp_ = inp.split()
                    try:
                        if inp == 'Chat':
                            if not self.check_firewall(CHAT_SERVER_PORT):
                                print('Packet dropped due to firewall issues.')
                            else:
                                self.connection.connect(('127.0.0.1', CHAT_SERVER_PORT))
                                self.state = State.chat
                        elif inp == 'Stream':
                            if not self.check_firewall(STREAM_SERVER_PORT):
                                print('Packet dropped due to firewall issues.')
                            else:
                                self.connection.connect(('127.0.0.1', STREAM_SERVER_PORT))
                                self.state = State.stream
                        elif inp_[0] == 'Chat' or inp_[0] == 'Stream':
                            proxy_port = int(inp_[2])
                            if not self.check_firewall(proxy_port):
                                print('Packet dropped due to firewall issues.')
                            else:
                                forward_port = str(CHAT_SERVER_PORT) if inp_[0] == 'Chat' else str(STREAM_SERVER_PORT)
                                self.proxy = proxy_port
                                self.connection.connect(('127.0.0.1', proxy_port))
                                self.connection.send(forward_port.encode('ascii'))
                                time.sleep(0.25)
                                self.state = State.chat if inp_[0] == 'Chat' else State.stream
                        else:
                            print('Invalid message')
                    except:
                        # traceback.print_exc()
                        print('Invalid message')
                        traceback.print_exc()
                elif self.state == State.chat:
                    if self.chat_state == ChatStates.login_signup_menu:
                        self.chat_login_signup_menu()
                        command = input()
                        self.connection.send(command.encode('ascii'))
                        if command == '1':
                            self.signup()
                        elif command == '2':
                            self.login()
                        elif command == '3':
                            pass
                            # TODO exit
                        else:
                            print('The command must be an integer from 1 to 3.')
                    elif self.chat_state == ChatStates.mailbox:
                        print('Enter \'0\' to go back to main menu.')
                        count += 1
                        if count > 20:
                            break
                        usernames = self.get_usernames()
                        command = input().strip()
                        self.connection.send(command.encode('ascii'))
                        if command == '0':
                            self.chat_state = ChatStates.login_signup_menu
                        elif command in usernames:
                            self.chat_state = ChatStates.chat
                    elif self.chat_state == ChatStates.chat:
                        self.load_x()
                        # receive_new_message = threading.Thread(target=self.receive_msg, args=())
                        # receive_new_message.start()
                        while True:
                            command = input()
                            self.connection.send(command.encode('ascii'))
                            if command[0] == '/':
                                if re.search('^load_\d+$', command[1:]):
                                    self.load_x()
                                elif command[1:] == 'exit':
                                    self.chat_state = ChatStates.mailbox
                                    break


                elif self.state == State.stream:
                    if self.video_request_state == VideoRequestState.not_started:
                        # send request to get list of videos
                        self.connection.send('list of videos'.encode('ascii'))

                        self.video_stream_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        self.audio_stream_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                        if self.proxy is not None:
                            self.video_stream_socket.connect(('127.0.0.1', self.proxy))
                            self.audio_stream_socket.connect(('127.0.0.1', self.proxy))
                            self.video_stream_socket.send(str(STREAM_SERVER_PORT).encode('ascii'))
                            self.audio_stream_socket.send(str(STREAM_SERVER_PORT).encode('ascii'))
                        else:
                            self.video_stream_socket.connect(('127.0.0.1', STREAM_SERVER_PORT))
                            self.audio_stream_socket.connect(('127.0.0.1', STREAM_SERVER_PORT))

                        self.video_request_state = VideoRequestState.idle
                        self.wait_for_video_list()
                    elif self.video_request_state == VideoRequestState.pending_for_list:
                        print("Please enter video id:")
                        video_id = input()
                        is_correct = self.check_video_id(video_id)
                        if is_correct:
                            if video_id == '0':
                                self.video_request_state = VideoRequestState.not_started
                                self.state = State.main_menu
                                self.connection.close()
                            else:
                                self.video_request_state = VideoRequestState.idle

                                video_stream_message = "{}{}{}".format(VIDEO_SOCKET, SEPARATOR, video_id)
                                audio_stream_message = "{}{}{}".format(AUDIO_SOCKET, SEPARATOR, video_id)

                                self.video_stream_socket.send(
                                    video_stream_message.encode('ascii'))
                                self.audio_stream_socket.send(
                                    audio_stream_message.encode('ascii'))
                                time.sleep(2)

                                recv_aud_thread = threading.Thread(target=self.receive_audio, args=())
                                recv_aud_thread.start()
                                self.receive_video()


                        else:
                            print("Invalid Video Id")

            except Exception:
                traceback.print_exc()
                # print("exception????")
                if self.connection is not None:
                    self.connection.close()
                break

    def receive_audio(self):

        q = queue.Queue(maxsize=2000)

        BUFF_SIZE = 65536
        p = pyaudio.PyAudio()
        CHUNK = 4 * 1024
        stream = p.open(format=p.get_format_from_width(2),
                        channels=2,
                        rate=44100,
                        output=True,
                        frames_per_buffer=CHUNK)

        while True:
            frame = self.audio_stream_socket.recv(4 * 1024)
            stream.write(frame)

    def chat_login_signup_menu(self):
        print('1. Sign Up\n2. Login\n3. Exit')

    def signup(self):
        while True:
            print('Please enter your username.')
            username = input()
            if username == '0':
                # Todo: change this message to just invalid
                print('This username is already existed or invalid. Please enter another one.')
            else:
                self.connection.send(username.encode('ascii'))
                username_check = self.connection.recv(4096).decode('ascii')
                print(username_check)
                if username_check == 'Please enter your password.':
                    self.username = username
                    break
        password = input()
        self.password = password
        self.connection.send(password.encode('ascii'))

    def login(self):
        print('Please enter your username.')
        username = input()
        print('Please enter your password.')
        password = input()
        self.connection.send(username.encode('ascii'))
        time.sleep(0.2)
        self.connection.send(password.encode('ascii'))
        log_in_check = self.connection.recv(4096).decode('ascii')
        print(log_in_check)
        if log_in_check != 'Incorrect username or password.':
            self.chat_state = ChatStates.mailbox

    def get_usernames(self):
        usernames = []
        recv_message = self.connection.recv(4096).decode('ascii')

        users_messages = recv_message.split(SEPARATOR)

        for msg in users_messages:
            msg = msg.split()
            usernames.append(msg[0])
            if int(msg[1]):
                print(f'{msg[0]} ({int(msg[1])})')
            else:
                print(msg[0])
        return usernames

    def receive_msg(self):
        while True:
            self.load_x()
            if self.chat_state != ChatStates.chat:
                break

    def load_x(self):
        message_count = int(self.connection.recv(4096).decode('ascii'))
        for i in range(message_count):
            msg = self.connection.recv(4096).decode('ascii')
            first_space = msg.find(' ')
            sender, m = msg[:first_space], msg[first_space + 1:]
            if sender != self.username:
                print(f'({sender}) {m}')
            else:
                print(m)

    def receive_video(self):
        print("receiving video...")
        # Todo: receive video

        data = b""
        payload_size = struct.calcsize("Q")

        print("For quit streaming, you can click 'q' key...")
        while True:
            while len(data) < payload_size:
                packet = self.video_stream_socket.recv(4 * 1024)  # 4K
                if not packet: break
                data += packet
            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack("Q", packed_msg_size)[0]

            while len(data) < msg_size:
                data += self.video_stream_socket.recv(4 * 1024)
            frame_data = data[:msg_size]
            data = data[msg_size:]
            frame = pickle.loads(frame_data)
            cv2.imshow("RECEIVING VIDEO", frame)
            if cv2.waitKey(25) & 0xFF == ord('q'):
                self.end_streaming()
                break

    def end_streaming(self):
        print("stream ended")
        cv2.destroyAllWindows()
        cv2.waitKey(1)
        self.video_stream_socket.close()
        self.audio_stream_socket.close()
        time.sleep(1)
        self.video_request_state = VideoRequestState.not_started

    def check_video_id(self, vid_id):
        if not number_pattern.match(vid_id):
            return False
        if int(vid_id) < 0 or int(vid_id) > self.videos_num:
            return False
        return True

    def wait_for_video_list(self):
        recv_message = self.connection.recv(1024).decode('ascii').strip().split(SEPARATOR)
        self.videos_num = int(recv_message[0])

        print("-------- List Of Videos ({}) --------".format(self.videos_num))
        print("0. Exit Stream Server")
        print(recv_message[1])

        self.video_request_state = VideoRequestState.pending_for_list

    def check_firewall(self, port):
        if self.firewall_type is FirewallType.blacklist:
            return port not in self.ports
        else:
            return port in self.ports

    def firewall_change(self, command):
        # global firewall_type, ports
        ls = command.split()
        try:
            if command == 'activate blacklist firewall':
                self.firewall_type = FirewallType.blacklist
                self.ports = []
            elif command == 'activate whitelist firewall':
                self.firewall_type = FirewallType.whitelist
                self.ports = []
            else:
                port_num = int(ls[2])
                if (ls[0] == 'open' and self.firewall_type == FirewallType.blacklist) or (
                        ls[0] == 'close' and self.firewall_type == FirewallType.whitelist):
                    if port_num in self.ports:
                        self.ports.remove(port_num)
                elif (ls[0] == 'close' and self.firewall_type == FirewallType.blacklist) or (
                        ls[0] == 'open' and self.firewall_type == FirewallType.whitelist):
                    if port_num not in self.ports:
                        self.ports.append(port_num)
                elif ls[0] == 'check':
                    if (self.firewall_type == FirewallType.blacklist and port_num in self.ports) or (
                            self.firewall_type == FirewallType.whitelist and port_num not in self.ports):
                        print('This port is closed.')
                    else:
                        print('This port is open.')
                else:
                    print('Invalid command.')
        except:
            print('Invalid command.')


if __name__ == '__main__':
    client = Client()
