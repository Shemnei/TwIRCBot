import re

import time

import master


class IRCPlugin(master.Plugin):

    COOL_DOWN = 10

    def __init__(self):
        super().__init__()
        self.__last_used = None

    def get_regex(self):
        return r"(@.* )?:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :!hello"

    def cmd(self, line):
        if not self.__last_used or (time.time() - self.__last_used > IRCPlugin.COOL_DOWN):
            user = re.search(r":\w+!", line)
            user = user.group(0).strip(":!").title()
            self.connection.add_chat_msg("Hello there %s" % user)
            self.__last_used = time.time()

    def get_description(self):
        return "!hello - I'm a friendly bot"
