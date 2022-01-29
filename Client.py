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
proxy = None
state = State.main_menu
connection = None

password = input('Please enter a password, this will be used for further changes in the firewall of the system.\n')


def send_via_proxy(message, dest_port):
    pass


def receive_via_proxy():
    pass


while True:
    if state == State.main_menu:
        pass
    elif state == State.admin:
        pass
    elif state == State.user:
        pass
    elif state == State.chat:
        pass
    elif state == State.stream:
        pass
