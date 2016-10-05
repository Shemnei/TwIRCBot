import re

import master


class IRCPlugin(master.Plugin):

    def get_regex(self):
        return r"(@.* )?:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :!close$"

    def cmd(self, line):
        user = re.search(r":\w+!", line).group(0).strip(":!").lower()
        if user == self.config["connection"]["nick_name"].lower() or user == self.config["connection"]["channel"].lower():
            self.bot.stop()

    def get_description(self):
        return "!close - Terminates bot"
