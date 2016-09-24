import os
import subprocess

import gtts
import re

import master


class IRCPlugin(master.Plugin):

    def __init__(self):
        super().__init__()
        self.mp3_path = os.path.join(os.path.dirname(__file__), "t2s.mp3")

    def get_regex(self):
        return r":\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :!t2s"

    def cmd(self, line):
        line = re.sub(self.get_regex(), "", line)
        if len(line) > 0:
            tts = gtts.gTTS(text=line, lang='en')
            tts.save(self.mp3_path)
            os.system("start %s" % self.mp3_path)

    def get_description(self):
        return "!t2s [text] - Converts text to audio and plays it"

    def on_close(self):
        super().on_close()
        if os.path.isfile(self.mp3_path):
            print("T2S: Cleaning up")
            os.remove(self.mp3_path)

