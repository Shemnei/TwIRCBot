import re

import time

import master


class IRCPlugin(master.Plugin):

    COOL_DOWN = 10

    def __init__(self):
        super().__init__()
        self.__last_used = None

    def get_regex(self):
        return r"(@.* )?:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :!(\w+)$"

    def cmd(self, line):
        if not self.__last_used or (time.time() - self.__last_used > IRCPlugin.COOL_DOWN):

            name = re.sub(r"(@.* )?:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :!", "", line)

            if name == "youtube":
                self.connection.add_chat_msg("I am on youtube: www.youtube.com")
            elif name == "twitter":
                self.connection.add_chat_msg("I am on twitter: www.twitter.com")

            self.__last_used = time.time()