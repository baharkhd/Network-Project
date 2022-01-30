import socket
import threading
from enum import Enum


class FirewallType(Enum):
    blacklist = 0
    whitelist = 1


class State(Enum):
    main_menu = 0
    admin = 1
    user = 2
    chat = 3
    stream = 4


ports = []
firewall_type = FirewallType.blacklist
proxy = False
state = State.main_menu
connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

password = input('Please enter a password, this will be used for further changes in the firewall of the system.\n')


def check_firewall(port):
    if firewall_type is FirewallType.blacklist:
        return port not in ports
    else:
        return port in ports


def firewall_change(command):
    global firewall_type, ports
    ls = command.split()
    try:
        if command == 'activate blacklist firewall':
            firewall_type = FirewallType.blacklist
            ports = []
        elif command == 'activate whitelist firewall':
            firewall_type = FirewallType.whitelist
            ports = []
        else:
            port_num = int(ls[2])
            if (ls[0] == 'open' and firewall_type == FirewallType.blacklist) or (
                    ls[0] == 'close' and firewall_type == FirewallType.whitelist):
                if port_num in ports:
                    ports.remove(port_num)
            elif (ls[0] == 'close' and firewall_type == FirewallType.blacklist) or (
                    ls[0] == 'open' and firewall_type == FirewallType.whitelist):
                if port_num not in ports:
                    ports.append(port_num)
            elif ls[0] == 'check':
                if (firewall_type == FirewallType.blacklist and port_num in ports) or (
                        firewall_type == FirewallType.whitelist and port_num not in ports):
                    print('This port is closed.')
                else:
                    print('This port is open.')
            else:
                print('Invalid command.')
    except:
        print('Invalid command.')


while True:
    try:
        if state == State.main_menu:
            print('1. Connect to external servers.\n2. Login as admin.\n3. Exit.')
            try:
                inp = int(input())
                if inp > 3 or inp < 1:
                    print('The command must be an integer from 1 to 3.')
                    continue
                if inp == 1:
                    state = State.user
                elif inp == 2:
                    state = State.admin
                else:
                    break
            except:
                print('The command must be an integer from 1 to 3.')

        elif state == State.admin:
            print('Please enter your password:')
            inp = input()
            while inp != password:
                print('Incorrect password. Try again ot type /exit to exit to main menu.')
                inp = input()
                if inp == '/exit':
                    state = State.main_menu
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
                    state = State.main_menu
                    break
                firewall_change(inp)
        elif state == State.user:
            print('1. Chat\n2. Stream')
            inp = input()
            inp_ = inp.split()
            try:
                if inp == 'Chat':
                    if not check_firewall(5050):
                        print('Packet dropped due to firewall issues.')
                    else:
                        connection.connect(('127.0.0.1', 5050))
                        state = State.chat
                elif inp == 'Stream':
                    if not check_firewall(5060):
                        print('Packet dropped due to firewall issues.')
                    else:
                        connection.connect(('127.0.0.1', 5060))
                        state = State.stream
                elif inp_[0] == 'Chat' or inp_[0] == 'Stream':
                    proxy_port = int(inp_[2])
                    if not check_firewall(proxy_port):
                        print('Packet dropped due to firewall issues.')
                    else:
                        forward_port = '5050' if inp_[0] == 'Chat' else '5060'
                        proxy = True
                        connection.connect(('127.0.0.1', proxy_port))
                        connection.send(forward_port.encode('ascii'))
                        state = State.chat if inp_[0] == 'Chat' else State.stream
                else:
                    print('Invalid message')
            except:
                print('Invalid message')
        elif state == State.chat:
            pass
        elif state == State.stream:
            pass
    except:
        if connection is not None:
            connection.close()
        print('An exception occurred.')
        break
