import logging
import os
import threading

import gtts

import master

logger = logging.getLogger(__name__)


class IRCPlugin(master.CommandPlugin):

    COMMAND = "!t2s"
    ARGS = "[text]"
    DESCRIPTION = "Converts text to audio and plays it"
    PERMISSION_LEVEL = 2
    ADD_TO_HELP = True

    CURRENCY_COST = 5
    COOL_DOWN = 30

    def __init__(self):
        super().__init__()
        self.mp3_path = os.path.join(os.path.dirname(__file__), "t2s.mp3")
        self.__lang = None

    def get_regex(self):
        return r"PRIVMSG #\w+ :!t2s \w+"

    def cmd(self, message):
        if self.is_valid_request(message.user):
            text = message.msg[5:]
            if len(text) > 0:
                logger.log(logging.DEBUG, "@%s -> t2s %s" % (str(message.user), message.msg[5:]))
                threading.Thread(target=self.text_2_speech, args=(message.msg[5:],), name="text_to_speech_thread").start()

    def text_2_speech(self, text):
        tts = gtts.gTTS(text=text, lang=self.__lang)
        tts.save(self.mp3_path)
        os.system("start %s" % self.mp3_path)

    def on_load(self, bot):
        super().on_load(bot)
        self.__lang = self.config.config["plugin_settings"]["lang_t2s"] or "en"

    def on_close(self):
        super().on_close()
        if os.path.isfile(self.mp3_path):
            logger.log(logging.DEBUG, "T2S Cleaned File")
            os.remove(self.mp3_path)

