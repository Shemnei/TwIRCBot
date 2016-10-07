import os
import re
import time

import gtts

import master


class IRCPlugin(master.CommandPlugin):

    COOL_DOWN = 30

    def __init__(self):
        super().__init__()
        self.mp3_path = os.path.join(os.path.dirname(__file__), "t2s.mp3")
        self.__lang = None
        self.__last_used = None

    def get_regex(self):
        return r"(@.* )?:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :!t2s "

    def cmd(self, message):
        if not self.__last_used or (time.time() - self.__last_used > IRCPlugin.COOL_DOWN):

            if message.user[1] >= self.data_manager.PermissionLevel.subscriber:

                text = message.msg.replace("!t2s ", '')
                if len(text) > 0:
                    tts = gtts.gTTS(text=text, lang=self.__lang)
                    tts.save(self.mp3_path)
                    os.system("start %s" % self.mp3_path)
                self.__last_used = time.time()

    def on_load(self, bot):
        super().on_load(bot)
        self.__lang = self.bot.get_config_manager()["general"]["lang_t2s"] or "en"

    def get_description(self):
        return "!t2s [text] - Converts text to audio and plays it"

    def on_close(self):
        super().on_close()
        if os.path.isfile(self.mp3_path):
            print("T2S: Cleaning up")
            os.remove(self.mp3_path)

