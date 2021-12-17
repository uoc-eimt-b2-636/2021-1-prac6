import array
import subprocess
import socket
import time


USERNAME = "asamam"
HOST = "34.242.114.191"
PORT_SPEECH_TO_TEXT = 5001
PORT_NODERED = 5002

byte_array = array.array('B')
audio_file = open("output.wav", 'rb')
byte_array.frombytes(audio_file.read())
print(len(byte_array))
audio_file.close()

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT_SPEECH_TO_TEXT))
    texto = '{"username": "' + USERNAME + '"}'
    s.sendall(texto.encode())
    time.sleep(2)
    s.sendall(byte_array)

    
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT_NODERED))
    data = s.recv(1024)
    print('Received', repr(data))
    if data == b'z':
        print("HACER BEEP!!")
        subprocess.call(["paplay", "/usr/share/sounds/speech-dispatcher/test.wav"])
    elif data == b'r':
        print("\033[31m")
        subprocess.call("clear")
    elif data == b'g':
        print("\033[32m")
        subprocess.call("clear")
    elif data == b'b':
        print("\033[32m")
        subprocess.call("clear")
    elif data == b'e':
        s.sendall(bytearray([0,1,2,3,4,5]))
        
    


