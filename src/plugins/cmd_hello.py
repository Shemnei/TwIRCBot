import time

import master


class IRCPlugin(master.CommandPlugin):

    COOL_DOWN = 10

    def __init__(self):
        super().__init__()
        self.__last_used = None

    def get_regex(self):
        return r"PRIVMSG #\w+ :!hello$"

    def cmd(self, message):
        if not self.__last_used or (time.time() - self.__last_used > IRCPlugin.COOL_DOWN):
            user = message.user[0]
            if message.tags and message.tags.get["display-name", None]:
                user = message.tags["display-name"]
            self.connection.add_chat_msg("Hello there %s" % user)
            self.__last_used = time.time()

    def get_description(self):
        return "!hello - I'm a friendly bot"
