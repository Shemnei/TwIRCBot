import re

import master


class IRCPlugin(master.Plugin):

    def get_regex(self):
        return r":\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :!changec"

    def cmd(self, line):
        channel = re.sub(self.get_regex(), "", line).strip()
        if channel:
            print("DEBUG: CHANGING CHANNELS")
            self.connection.join_channel(channel.lower())

    def get_description(self):
        return "!changec [channel] - Switches to that channel (leaves current)"
