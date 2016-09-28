import re

import master


class IRCPlugin(master.Plugin):

    def get_regex(self):
        return r"(@.* )?:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :!changec"

    def cmd(self, line):
        channel = re.sub(self.get_regex(), "", line).strip()
        match = re.search(r"^([a-zA-Z0-9_]+)$", channel)
        if match:
            print(self.connection.Color.GREEN + "DEBUG: CHANGING CHANNELS" + self.connection.Color.RESET)
            self.connection.join_channel(match.group().lower())
        else:
            print(self.connection.Color.BRIGHT_RED + "DEBUG: INVALID CHANNEL NAME" + self.connection.Color.RESET)

    def get_description(self):
        return "!changec [channel] - Switches to that channel (leaves current)"
