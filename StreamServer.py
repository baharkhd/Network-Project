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
import time
import moviepy.editor as mp
from commons import SEPARATOR
import wave

from commons import STREAM_SERVER_PORT

VIDEO_SOCKET = 'VIDEO_SOCKET'
AUDIO_SOCKET = "AUDIO_SOCKET"

video_stream_pattern = re.compile("^{}{}[0-9]+$".format(VIDEO_SOCKET, SEPARATOR))
audio_stream_pattern = re.compile("^{}{}[0-9]+$".format(AUDIO_SOCKET, SEPARATOR))


class StreamServer:
    videos = list()
    sending_video_lock = threading.Lock()

    stream_thread = None

    def __init__(self):
        addr = ('127.0.0.1', STREAM_SERVER_PORT)

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

            client_thread = threading.Thread(target=self.handle, args=(client, address))
            client_thread.start()

    def init_videos(self):
        videos_path = os.path.join(os.getcwd(), 'videos')

        for i, filename in enumerate(os.listdir(videos_path)):
            video = Video(name=filename, id=i + 1)
            self.videos.append(video)

            self.init_audio(video.name)

    def init_audio(self, filename):
        videos_path = os.path.join(os.getcwd(), 'videos')
        audios_path = os.path.join(os.getcwd(), 'audios')

        video_path = os.path.join(videos_path, filename)

        audio_filename = filename.replace(".mp4", ".wav")
        audio_path = os.path.join(audios_path, audio_filename)

        my_clip = mp.VideoFileClip(video_path)
        my_clip.audio.write_audiofile(audio_path)


    def handle(self, client, address):
        while True:
            message = client.recv(4096).decode('ascii').strip()
            print("* message received from client {}: ".format(address), message, type(message))

            number_pattern = re.compile("^[0-9]+$")

            if message == 'list of videos':
                print("here in list of videos")
                list_of_videos = '{}'.format(str(len(self.videos)))
                list_of_videos += SEPARATOR
                for video in self.videos:
                    list_of_videos += '{}. {}\n'.format(video.id, video.name)
                client.send(list_of_videos.encode('ascii'))
            elif number_pattern.match(message):
                # client has requested a video
                self.sending_video_lock.acquire()
                print("Client requested video with id {}".format(message))
                video_id = int(message)
                stream_thread = threading.Thread(target=self.send_vid, args=(client, video_id))
                stream_thread.start()
                self.stream_thread = stream_thread
            elif video_stream_pattern.match(message):
                # this is video socket
                parts = message.split(SEPARATOR)

                video_id = int(parts[1])
                video_stream_thread = threading.Thread(target=self.send_vid, args=(client, video_id))
                video_stream_thread.start()
                self.video_stream_thread = video_stream_thread
            elif audio_stream_pattern.match(message):
                # this is audio socket
                parts = message.split(SEPARATOR)

                video_id = int(parts[1])
                audio_stream_thread = threading.Thread(target=self.send_audio, args=(client, video_id))
                audio_stream_thread.start()
                self.audio_stream_thread = audio_stream_thread
            elif message == "stop streaming":
                print("here? stop streaming")
            else:
                client.send('Invalid Command'.encode('ascii'))

    def send_audio(self, client, vid_id):
        print("Sending Audio ...")
        video = self.videos[vid_id - 1]
        audio_name = video.name.replace(".mp4", ".wav")
        audio_path = os.path.join(os.getcwd(), 'audios', audio_name)

        BUFF_SIZE = 65536

        CHUNK = 4 * 1024
        wf = wave.open(audio_path)

        data = None
        sample_rate = wf.getframerate()

        while True:
            data = wf.readframes(CHUNK)
            client.sendall(data)
            time.sleep(0.8 * CHUNK / sample_rate)

    def send_vid(self, client, vid_id):
        print("Sending Video ...")

        video = self.videos[vid_id - 1]
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
                break
        except:
            print("exception occured! (video)")

        print("-------- stopped streaming")
        if vid:
            vid.release()
            cv2.destroyAllWindows()


if __name__ == "__main__":
    stream_server = StreamServer()