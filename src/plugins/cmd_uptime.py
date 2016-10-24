import datetime
import json
import logging
import threading
import time
import urllib.request

import master

logger = logging.getLogger(__name__)


class IRCPlugin(master.CommandPlugin):

    COMMAND = "!uptime"
    ARGS = ""
    DESCRIPTION = "Stream uptime"
    PERMISSION_LEVEL = 0
    ADD_TO_HELP = True

    COOL_DOWN = 10
    BASE_URL = "https://api.twitch.tv/kraken/streams/%s?client_id=%s"

    def __init__(self):
        super().__init__()
        self.__current_stream_start = None
        self.__current_channel = None
        self.__last_fetched = None

    def get_regex(self):
        return r"PRIVMSG #\w+ :!uptime$"

    def cmd(self, message):
        if self.is_valid_request(message.user):

            if not self.__current_stream_start:
                logger.log(logging.DEBUG, "@%s -> uptime [%s/offline]" % (str(message.user), self.__current_channel))
                self.connection.add_chat_msg("Stream is offline")
            else:
                current = datetime.datetime.fromtimestamp(time.mktime(time.gmtime())) - datetime.timedelta(hours=1)
                diff = current - self.__current_stream_start
                logger.log(logging.DEBUG, "@%s -> uptime [%s/%s]" % (str(message.user), self.__current_channel, diff))
                self.connection.add_chat_msg("Stream online for: %s" % (current - self.__current_stream_start))

            # TODO make it message independent
            if time.time() - self.__last_fetched > 300:
                threading.Thread(name="uptime_request_thread", target=self.__get_stream_uptime).start()

    def __get_stream_uptime(self):
        logger.log(logging.DEBUG, "@uptime -> fetching uptime[%s]" % self.__current_channel)
        data = urllib.request.urlopen(IRCPlugin.BASE_URL % (self.__current_channel,
                                                            self.config.config["connection"]["client_id"])).read()
        jo = json.loads(data.decode())
        if jo["stream"]:
            self.__current_stream_start = datetime.datetime.strptime(jo["stream"]["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        else:
            self.__current_stream_start = None
        self.__last_fetched = time.time()

    def on_channel_change(self, new_channel):
        super().on_channel_change(new_channel)
        self.__current_stream_start = None
        self.__current_channel = new_channel
        threading.Thread(name="uptime_request_thread", target=self.__get_stream_uptime).start()
