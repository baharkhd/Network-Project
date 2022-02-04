import socket
import threading
from enum import Enum
from User import User
import re
from StreamServer import SEPARATOR
import pickle
import struct
import imutils
import cv2
import time
import queue
import pyaudio
import traceback
from commons import STREAM_SERVER_PORT

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


class Client(User):
    ports = []
    firewall_type = FirewallType.blacklist
    proxy = False
    state = State.main_menu

    video_request_state = VideoRequestState.not_started
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
        self.password = password
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
                    while inp != self.password:
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
                    print('1. Chat\n2. Stream')
                    inp = input()
                    inp_ = inp.split()
                    try:
                        if inp == 'Chat':
                            if not self.check_firewall(5050):
                                print('Packet dropped due to firewall issues.')
                            else:
                                self.connection.connect(('127.0.0.1', 5050))
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
                                forward_port = '5050' if inp_[0] == 'Chat' else 'STREAM_SERVER_PORT'
                                self.proxy = True
                                self.connection.connect(('127.0.0.1', proxy_port))
                                self.connection.send(forward_port.encode('ascii'))
                                self.state = State.chat if inp_[0] == 'Chat' else State.stream
                        else:
                            print('Invalid message')
                    except:
                        print('Invalid message')
                elif self.state == State.chat:
                    print("here in chat state")
                    pass
                elif self.state == State.stream:
                    if self.video_request_state == VideoRequestState.not_started:
                        # send request to get list of videos
                        self.connection.send('list of videos'.encode('ascii'))

                        self.video_stream_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        self.audio_stream_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

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
                if self.connection is not None:
                    self.connection.close()

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
            frame= self.audio_stream_socket.recv(4 * 1024)
            stream.write(frame)

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
        print("received message : ", recv_message)
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
