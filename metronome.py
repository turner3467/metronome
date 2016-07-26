#! /usr/bin/env python

import pyaudio
import wave
import time
import argparse
import sys
import select
import termios


# setup key press detection
class KeyPoller():
    def __enter__(self):
        # Save the terminal settings
        self.fd = sys.stdin.fileno()
        self.new_term = termios.tcgetattr(self.fd)
        self.old_term = termios.tcgetattr(self.fd)

        # New terminal setting unbuffered
        self.new_term[3] = (self.new_term[3] & ~termios.ICANON & ~termios.ECHO)
        termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.new_term)

        return self

    def __exit__(self, type, value, traceback):
        termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.old_term)

    def poll(self):
        dr, dw, de = select.select([sys.stdin], [], [], 0)
        if not dr == []:
            return sys.stdin.read(1)
        return None

# parse cli arguments
parser = argparse.ArgumentParser()
parser.add_argument("-b", "--bpm", default=120)
parser.add_argument("-t", "--time_sig", default="4/4")
args = parser.parse_args()

TIME_SIG = args.time_sig
BPM = args.bpm

beat_delay = 60 / int(BPM)
beat_count = int(TIME_SIG.split("/")[0])

# prepare audio files
p = pyaudio.PyAudio()

high = wave.open(r"High Seiko SQ50.wav", "rb")
low = wave.open(r"Low Seiko SQ50.wav", "rb")

stream = p.open(format=p.get_format_from_width(high.getsampwidth()),
                channels=high.getnchannels(),
                rate=high.getframerate(),
                output=True)

high_data = high.readframes(2048)
low_data = low.readframes(2048)

with KeyPoller() as key_poller:
    beat = 0
    while True:
        c = key_poller.poll()
        if beat % beat_count == 0:
            stream.write(high_data)
        else:
            stream.write(low_data)
        if not c is None:
            if c == "q":
                break
            print(c)
        time.sleep(beat_delay)
        beat += 1

stream.close()
p.terminate()
