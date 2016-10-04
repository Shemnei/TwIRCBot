import re

import master


class IRCPlugin(master.Plugin):

    def get_regex(self):
        return r"(@.* )?:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :!(\w+)$"

    def cmd(self, line):
        name = re.sub(r"(@.* )?:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :!", "", line)

        if name == "youtube":
            self.connection.add_chat_msg("I am on youtube: www.youtube.com")
        elif name == "twitter":
            self.connection.add_chat_msg("I am on twitter: www.twitter.com")