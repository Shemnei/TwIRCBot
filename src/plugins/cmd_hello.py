import importlib

import re

import master


class IRCPlugin(master.Plugin):

    def get_regex(self):
        return r":\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :!hello"

    def cmd(self, line):
        user = re.search(r":\w+!", line)
        user = user.group(0).strip(":!").title()
        self.connection.add_chat_msg("Hello there %s" % user)

    def get_description(self):
        return "!hello - I'm a friendly bot"
