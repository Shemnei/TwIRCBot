import re

import master


class IRCPlugin(master.CommandPlugin):

    def get_regex(self):
        return r"(@.* )?:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :!close$"

    def cmd(self, message):
        if message.user[0] == self.config["connection"]["nick_name"].lower() or message.user[0] == self.config["connection"]["channel"].lower():
            self.bot.stop()

    def get_description(self):
        return "!close - Terminates bot"
