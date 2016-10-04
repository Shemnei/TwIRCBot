import time

import master


class IRCPlugin(master.Plugin):

    COOL_DOWN = 10

    def __init__(self):
        super().__init__()
        self.__last_used = None

    def get_regex(self):
        return r"(@.* )?:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :!example"

    def cmd(self, line):
        if not self.__last_used or (time.time() - self.__last_used > IRCPlugin.COOL_DOWN):
            self.connection.add_chat_msg("PONG")
            self.__last_used = time.time()

    def on_refresh(self):
        print("Custom Refresh")

    def on_close(self):
        print("Example SHUTDOWN [%s]" % self.__module__)

    def get_description(self):
        return "!example - needs space between cmd and description for help to work"