import pyaudio
import wave
import time

frames = []

def pyaudio_callback(in_data, frame_count, time_info, status):
    global frames
    frames.append(in_data)
    return (in_data, pyaudio.paContinue)

def main():
    global frames

    # Inicializamos Pyaudio
    p = pyaudio.PyAudio()

    # Abrimos un stream de audio
    stream = p.open(format = pyaudio.paInt16,
                    channels = 1,
                    rate = 8000,
                    input = True,
                    output = True,
                    frames_per_buffer = 1024,
                    stream_callback = pyaudio_callback)

    # Iniciamos el stream de audio
    stream.start_stream()

    # El hilo principal espera 5 segundos
    time.sleep(5)

    # Cerramos el stream de audio
    stream.stop_stream()
    stream.close()

    # Finalizamos Pyaudio
    p.terminate()

    # Utilizamos la libreria Wave para convertir a WAV 
    wf = wave.open("output.wav", 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
    wf.setframerate(8000)
    wf.writeframes(b''.join(frames))
    wf.close()


if __name__ == "__main__":
    main()