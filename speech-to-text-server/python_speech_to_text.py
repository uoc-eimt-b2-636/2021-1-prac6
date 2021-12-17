#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import importlib
importlib.reload(sys)
#sys.setdefaultencoding('utf-8')

import socket
import threading
import pyaudio
import socket
import errno
import time
import wave
import queue as Queue
import numpy as np
import os
import select
import io
import json
import paho.mqtt.client as mqtt


from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types

IP_ADDRESS  = "0.0.0.0"
TCP_DATA_PORT_NUMBER = 5001

CHUNK    = 512
BYTES    = 2 * CHUNK

RATE     = 8000
CHANNELS = 1
FORMAT   = pyaudio.paInt16

audio_frames = Queue.Queue()

wf = None

def audio_cb(in_data, frame_count, time_info, status): 
    global wf

    # Get next audio frame
    out = wf.readframes(frame_count)

    # Return audio frame for playback
    return (out, pyaudio.paContinue)


class ThreadedServer(object):
    def __init__(self, host, port):
            self.host = host
            self.port = port
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind((self.host, self.port))
            
            
    def listen(self):
        self.sock.listen(1)
        while True:
            client, address = self.sock.accept()
            client.settimeout(1)
            print('Got a data TCP connection from', address)
            threading.Thread(target = self.listenToClient,args = (client,address)).start()

    def listenToClient(self, client, address):
         global wf

         pa = pyaudio.PyAudio()
         print("Starting new thread")
         
         # Get TAG
         data = client.recv(1000);
         print("DATA VALUE") #=" + str(data))
         recv_json = json.loads(data.decode("utf-8", "ignore"))
         #print(json)
         usertag = recv_json['username']
         print("userTag: " + usertag)
         
         # Get Audio 
         is_finished = False
         while not (is_finished):
            try:
                data = client.recv(BYTES)
                if not(data):
                    is_finished = True
                    break
                else:
                      audio_frames.put(data)
            except:
                pass
            
         print("Close TCP socket")
         client.close()
         
         # ensure nobody is sending anything else 
         time.sleep(2)
         
         file_name = "audiofile_"+usertag+".wav"
         print("Using " + file_name )
         # Store audio frames
         if (not audio_frames.empty()):
            # Open output audio file
            audio_out = wave.open(file_name, 'wb')
            audio_out.setnchannels(CHANNELS)
            audio_out.setsampwidth(pa.get_sample_size(FORMAT))
            audio_out.setframerate(RATE)

            # Store frames in output audio file
            while not audio_frames.empty():
                try:
                    frame = audio_frames.get()
                    #data = np.fromstring(frame, dtype=np.int16).astype(np.int16)
                    audio_out.writeframes(frame)
                except:
                    pass

            # Close output audio file
            audio_out.close()

         # Close PyAudio
         pa.terminate() 
         
         # send to google
         print("Sending to Google Speech")
         client = speech.SpeechClient()

         with io.open(file_name, 'rb') as audio_file:
            content = audio_file.read()

         audio = types.RecognitionAudio(content=content)
         config = types.RecognitionConfig(
            encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=8000,
            language_code='es-ES')

         #operation = client.long_running_recognize(config, audio)

         #response = operation.result(timeout=90)
         response = client.recognize(config, audio)

         print("RESPONSE")
         try:
            for result in response.results:
                print('Transcript: {}'.format(result.alternatives[0]))
            resultado = response.results[0].alternatives[0].transcript
         except:		
            resultado = "transcripcion vacia"         
         # post to mqtt
         mqtt_client = mqtt.Client("client")
         mqtt_client.username_pw_set(username="admin",password="industria40")
         mqtt_client.connect(IP_ADDRESS)
         mqtt_message = "{\"Transcript\":  \"" + resultado + "\" }"
         #mqtt_message = "{\"Transcript\":  \"" + "sonido" + "\" }"
         print("mqtt_message="+mqtt_message)
         mqtt_client.publish(usertag, mqtt_message)
         
         # finished
if __name__ == "__main__":
    ThreadedServer(IP_ADDRESS,TCP_DATA_PORT_NUMBER ).listen()
