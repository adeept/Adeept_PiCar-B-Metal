#!/usr/bin/env python3

# Real-time speech recognition from a microphone with sherpa-onnx Python API
# with endpoint detection.
#
# Please refer to
# https://k2-fsa.github.io/sherpa/onnx/pretrained_models/index.html
# to download pre-trained models
import sys
import os
import time
import subprocess
import threading
import numpy as np
import sherpa_onnx

username = os.popen("echo ${SUDO_USER:-$(who -m | awk '{ print $1 }')}").readline().strip() # pi
user_home = os.popen(f'getent passwd {username} | cut -d: -f 6').readline().strip()        # home

dic_map = {
    "前进": "forward",
    "向前走": "forward",
    "后退": "backward",
    "向后走": "backward",
    "左转": "left",
    "左转弯": "left",
    "右转": "right",
    "右转弯": "right",
    "停止": "TS",
    "头向左转": "lookleft",
    "头向右转": "lookright",
    "抬起头": "up",
    "低下头": "down",
    "头部回正": "home",
    "头回正": "home",
    "HEAD UP": "up",
    "HEAD DOWN": "down", 
    "HEAD LEFT": "lookleft",
    "HEAD RIGHT": "lookright",
    "STOP": "TS",
    "HOME":"home",
    "FORWARD": "forward",
    "BACKWARD": "backward",
    "LEFT": "left",
    "TURN LEFT": "left",
    "RIGHT": "right",
    "TURN RIGHT": "right",
}

class Speech(threading.Thread):
    def __init__(self, control_callback, *args, **kwargs):
        self.SpeechMode = 'none'
        self.command = ''
        self.control_callback = control_callback
        self.recognizer = sherpa_onnx.OnlineRecognizer.from_transducer(
            tokens=f"{user_home}/sherpa-onnx/sherpa-onnx-streaming-zipformer-bilingual-zh-en-2023-02-20/tokens.txt",
            encoder=f"{user_home}/sherpa-onnx/sherpa-onnx-streaming-zipformer-bilingual-zh-en-2023-02-20/encoder-epoch-99-avg-1.onnx",
            decoder=f"{user_home}/sherpa-onnx/sherpa-onnx-streaming-zipformer-bilingual-zh-en-2023-02-20/decoder-epoch-99-avg-1.onnx",
            joiner=f"{user_home}/sherpa-onnx/sherpa-onnx-streaming-zipformer-bilingual-zh-en-2023-02-20/joiner-epoch-99-avg-1.onnx",
            num_threads=1,
            sample_rate=16000,
            feature_dim=80,
            enable_endpoint_detection=True,
            rule1_min_trailing_silence=2.4,
            rule2_min_trailing_silence=1.2,
            rule3_min_utterance_length=300,  # it essentially disables this rule
            provider="cpu"
        )
        self.cmd = [
            "arecord",
            "-D", "plughw:2,0",   # device card 2, subdevice 0, command: arecord -l
            "-f", "S16_LE",       # format
            "-r", "16000",        # supported sample rate
            "-c", "1",            # mono
            "-t", "raw", 
            "-q",                 # output raw audio
            "-"                   # output to stdout
        ]
        super(Speech, self).__init__(*args, **kwargs)
        self.__flag = threading.Event()
        self.__flag.clear()
        self.p = None

    def pause(self):
        self.SpeechMode = 'none'
        self.__flag.clear()
        # 关闭录音
        if self.p:
            try:
                self.p.terminate()
            except:
                pass
            self.p = None


    def resume(self):
        self.__flag.set()

    def speech(self):
        self.SpeechMode = 'speech'
        self.resume()

    def run(self):
        while True:
            self.__flag.wait()
            if self.SpeechMode == 'speech':
                self.SpeechProcessing()
            time.sleep(0.1)

    def SpeechProcessing(self):
        # The model is using 16 kHz, we use 48 kHz here to demonstrate that
        # sherpa-onnx will do resampling inside.
        sample_rate = 16000
        chunk_seconds = 0.2
        chunk_size = int(sample_rate * chunk_seconds)
        stream = self.recognizer.create_stream()
        # display = sherpa_onnx.Display()

        if self.p == None:
            self.p = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=chunk_size * 2)

        while self.SpeechMode == 'speech':
            data = self.p.stdout.read(chunk_size * 2)
            if not data:
                return 
            samples = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
            stream.accept_waveform(sample_rate, samples)
            while self.recognizer.is_ready(stream):
                self.recognizer.decode_stream(stream)

            # display.update_text(result)
            # display.display()

            if self.recognizer.is_endpoint(stream):
                result = self.recognizer.get_result(stream)
                if result:
                    self.command = dic_map.get(result, result)
                    print(f"{result} ==> {self.command}")


                    self.control_callback(self.command, None)
                    self.command = ''
                    # display.finalize_current_sentence()
                    # display.display()
                self.recognizer.reset(stream)


if __name__ == "__main__":

    speech = Speech()
    speech.daemon = True 
    speech.start() 
    speech.speech()  
    while 1:
        time.sleep(1)
