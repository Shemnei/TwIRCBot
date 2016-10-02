import datetime
import json
import time
import urllib.request

import master


class IRCPlugin(master.Plugin):

    BASE_URL = "https://api.twitch.tv/kraken/streams/%s?client_id=%s"

    def __init__(self):
        super().__init__()
        self.__current_stream_start = None
        self.__current_channel = None
        self.__offline = None

    def get_regex(self):
        return r"(@.* )?:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :!uptime$"

    def cmd(self, line):
        if self.__offline:
            print("Uptime: Offline")
            self.connection.add_chat_msg("Stream is offline")
        else:
            current = datetime.datetime.fromtimestamp(time.mktime(time.gmtime())) - datetime.timedelta(hours=1)
            print("Uptime: %s" % (current- self.__current_stream_start))
            self.connection.add_chat_msg("Stream online for: %s" % (current- self.__current_stream_start))

    def get_created_at(self):
        with urllib.request.urlopen(IRCPlugin.BASE_URL % (self.__current_channel, self.bot.get_config_manager()["connection"]["client_id"])) as c:
            content = c.read()
        jo = json.loads(content.decode())
        if jo["stream"]:
            self.__offline = False
            self.__current_stream_start = datetime.datetime.strptime(jo["stream"]["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        else:
            self.__offline = True

    def on_channel_change(self, new_channel):
        super().on_channel_change(new_channel)
        self.__current_stream_start = None
        self.__current_channel = new_channel
        self.__offline = None
        self.get_created_at()

    def get_description(self):
        return "!uptime - Stream uptime"
