import datetime
import json
import threading
import time
import urllib.request

import master


class IRCPlugin(master.CommandPlugin):

    COOL_DOWN = 10
    BASE_URL = "https://api.twitch.tv/kraken/streams/%s?client_id=%s"

    # TODO test speed
    def __init__(self):
        super().__init__()
        self.__current_stream_start = None
        self.__current_channel = None
        self.__sample_timestamp = None
        self.__last_used = None

    def get_regex(self):
        return r"(@.* )?:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :!uptime$"

    def cmd(self, message):
        if not self.__last_used or (time.time() - self.__last_used > IRCPlugin.COOL_DOWN):
            if not self.__current_stream_start:
                print("Uptime: Offline")
                self.connection.add_chat_msg("Stream is offline")
            else:
                current = datetime.datetime.fromtimestamp(time.mktime(time.gmtime())) - datetime.timedelta(hours=1)
                print("Uptime: %s" % (current - self.__current_stream_start))
                self.connection.add_chat_msg("Stream online for: %s" % (current - self.__current_stream_start))

            if time.time() - self.__sample_timestamp > 300:
                threading.Thread(name="uptime_request_thread", target=self.get_created_at).start()

            self.__last_used = time.time()

    def get_created_at(self):
        with urllib.request.urlopen(IRCPlugin.BASE_URL % (self.__current_channel, self.bot.get_config_manager()["connection"]["client_id"])) as c:
            content = c.read()
        jo = json.loads(content.decode())
        if jo["stream"]:
            self.__current_stream_start = datetime.datetime.strptime(jo["stream"]["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        else:
            self.__current_stream_start = None
        self.__sample_timestamp = time.time()

    def on_channel_change(self, new_channel):
        super().on_channel_change(new_channel)
        self.__current_stream_start = None
        self.__current_channel = new_channel
        threading.Thread(name="uptime_request_thread", target=self.get_created_at).start()

    def get_description(self):
        return "!uptime - Stream uptime"
