import datetime
import re

import master


class IRCPlugin(master.FilterPlugin):

    # maybe move to privmsg

    def get_regex(self):
        return r"(@.* )?:\w+!\w+@\w+\.tmi\.twitch\.tv WHISPER \w+ :"

    def cmd(self, message):
        user = message.user[0]
        if message.tags and message.tags["display-name"]:
            user = message.tags["display-name"]
        print("[" + datetime.datetime.now().strftime("%H:%M:%S") + "] " + self.connection.Color.BRIGHT_CYAN + user +
              " -> " + message.channel + ": " + message.msg + "\033[0m")
