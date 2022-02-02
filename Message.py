class Message:
    msg = ''
    date = None
    sender = None
    receiver = None

    def __init__(self, msg, date, sender, receiver):
        self.msg = msg
        self.date = date
        self.sender = sender
        self.receiver = receiver
