import datetime

import re

import master


class IRCPlugin(master.Plugin):

    _active = True

    def get_regex(self):
        if IRCPlugin._active:
            return r":\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :"
        else:
            return r"$ä"

    def cmd(self, line):
        user = re.search(r":\w+!", line)
        user = user.group(0).strip(":!").title()
        line = re.sub(self.get_regex(), "", line)
        print("[" + datetime.datetime.now().strftime("%H:%M:%S") + "] " + user + ": " + line)
