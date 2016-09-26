import datetime
import time
import re

import collections

import master


class IRCPlugin(master.Plugin):

    _active = True

    def get_regex(self):
        if IRCPlugin._active:
            return r"(@.* )?:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :"
        else:
            return r"$ä"

    def cmd(self, line):
        user = re.search(r":\w+!", line)
        user = user.group(0).strip(":!").title()
        title = ""
        if line.startswith('@'):
            tag_cmp = self.connection.TagCompound(line[:line.find(" ")])
            tmp = ""
            if tag_cmp.get_mod() == "1":
                tmp += "M/"
            if tag_cmp.get_subscriber() == "1":
                tmp += "S/"
            if tag_cmp.get_turbo() == "1":
                tmp += "T/"
            if tag_cmp.get_bits():
                tmp += tag_cmp.bits()
            tmp = tmp.strip("/")
            title = "| (%s) " % tmp
            if tag_cmp.get_displayname():
                user = tag_cmp.get_displayname()

        line = re.sub(self.get_regex(), "", line)
        print("[" + datetime.datetime.now().strftime("%H:%M:%S") + "] " + title + user + ": " + line)


