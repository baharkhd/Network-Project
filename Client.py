import socket
import threading
from enum import Enum
from User import User


class FirewallType(Enum):
    blacklist = 0
    whitelist = 1


class State(Enum):
    main_menu = 0
    admin = 1
    user = 2
    chat = 3
    stream = 4


class Client(User):
    ports = []
    firewall_type = FirewallType.blacklist
    proxy = False
    state = State.main_menu

    def __init__(self):
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

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
                            if not self.check_firewall(5060):
                                print('Packet dropped due to firewall issues.')
                            else:
                                self.connection.connect(('127.0.0.1', 5060))
                                self.state = State.stream
                        elif inp_[0] == 'Chat' or inp_[0] == 'Stream':
                            proxy_port = int(inp_[2])
                            if not self.check_firewall(proxy_port):
                                print('Packet dropped due to firewall issues.')
                            else:
                                forward_port = '5050' if inp_[0] == 'Chat' else '5060'
                                self.proxy = True
                                self.connection.connect(('127.0.0.1', proxy_port))
                                self.connection.send(forward_port.encode('ascii'))
                                self.state = State.chat if inp_[0] == 'Chat' else State.stream
                        else:
                            print('Invalid message')
                    except:
                        print('Invalid message')
                elif self.state == State.chat:
                    pass
                elif self.state == State.stream:
                    pass
            except:
                if self.connection is not None:
                    self.connection.close()
                print('An exception occurred.')
                break

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