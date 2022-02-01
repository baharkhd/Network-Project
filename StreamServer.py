import socket
import threading
from Video import Video
from typing import List
import os
import cv2
from ffpyplayer.player import MediaPlayer
import re
import pickle
import struct
import imutils

SEPARATOR = "********"


class StreamServer:
    videos = list()

    def __init__(self):
        addr = ('127.0.0.1', 5060)

        self.init_videos()

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

    def init_videos(self):
        videos_path = os.path.join(os.getcwd(), 'videos')

        for i, filename in enumerate(os.listdir(videos_path)):
            # video_path = os.path.join(videos_path, filename)
            video = Video(name=filename, id=i + 1)
            self.videos.append(video)

    def handle(self, client):
        # Don't forget to include stop-stream feature in your code.
        # To send the video, You can create a new thread with function send_vid and look for incoming messages from client.

        while True:
            message = client.recv(4096).decode('ascii').strip()
            print("* message received from client: ", message)

            number_pattern = re.compile("^[0-9]+$")

            if message == 'list of videos':
                list_of_videos = '{}'.format(str(len(self.videos)))
                list_of_videos += SEPARATOR
                for video in self.videos:
                    list_of_videos += '{}. {}\n'.format(video.id, video.name)
                client.send(list_of_videos.encode('ascii'))
            elif number_pattern.match(message):
                # client has requested a video
                print("Client requested video with id {}".format(message))
                video_id = int(message)
                client_thread = threading.Thread(target=self.send_vid, args=(client, video_id))
                client_thread.start()
            else:
                client.send('Invalid Command'.encode('ascii'))

    def send_vid(self, client, vid_id):
        video = self.videos[vid_id - 1]
        # Todo: send video

        video_path = os.path.join(os.getcwd(), 'videos', video.name)
        try:
            while True:
                if client:
                    vid = cv2.VideoCapture(video_path)

                    while vid.isOpened():
                        img, frame = vid.read()
                        a = pickle.dumps(frame)
                        message = struct.pack("Q", len(a)) + a
                        client.sendall(message)
        except:
            print("exception occured!")
            vid.release()
            cv2.destroyAllWindows()


if __name__ == "__main__":
    stream_server = StreamServer()

    # videos_path = os.path.join(os.getcwd(), 'videos')
    #
    # for filename in os.listdir(videos_path):
    #     print(filename)
    #     video_path = os.path.join(videos_path, filename)
    #     cap = cv2.VideoCapture(os.path.join(videos_path, filename))
    #     player = MediaPlayer(video_path)
    #
    #     while cap.isOpened():
    #         ret, frame = cap.read()
    #         audio_frame, val = player.get_frame()
    #         if ret:
    #             if cv2.waitKey(25) & 0xFF == ord('q'):
    #                 break
    #             cv2.imshow('Frame',frame)
    #             if val != 'eof' and audio_frame is not None:
    #                 #audio
    #                 img, t = audio_frame
    #         else:
    #             break
    #     cap.release()
    #     cv2.destroyAllWindows()
