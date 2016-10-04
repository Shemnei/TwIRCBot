import datetime
import re

import master


class IRCPlugin(master.Plugin):

    # maybe move to privmsg

    def get_regex(self):
        return r"(@.* )?:\w+!\w+@\w+\.tmi\.twitch\.tv WHISPER \w+ :"

    def cmd(self, line):
        user = re.search(r":\w+!", line)
        user = user.group(0).strip(":!")
        target = re.search(r"R \w+ :", line)
        target = target.group(0).strip("R:").strip()
        if line.startswith('@'):
            tag_cmp = self.connection.parse_tags(line[:line.find(" ")])
            if tag_cmp.get("display-name", None):
                user = tag_cmp["display-name"]

        line = re.sub(self.get_regex(), "", line)
        print("[" + datetime.datetime.now().strftime("%H:%M:%S") + "] " + self.connection.Color.BRIGHT_CYAN + user +
              " -> " + target + ": " + line + "\033[0m")
