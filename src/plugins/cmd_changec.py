import re

import master

# ONLY FOR BOT SELF

class IRCPlugin(master.CommandPlugin):

    def get_regex(self):
        return r"(@.* )?:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :!changec"

    def cmd(self, message):
        if message.user[0] == self.config["connection"]["nick_name"].lower():

            channel = message.msg.replace("!changec", '').strip()
            match = re.search(r"^(\w+)$", channel)
            if match:
                print(self.connection.Color.GREEN + "DEBUG: CHANGING CHANNELS" + self.connection.Color.RESET)
                self.connection.join_channel(match.group().lower())
            else:
                print(self.connection.Color.BRIGHT_RED + "DEBUG: INVALID CHANNEL NAME" + self.connection.Color.RESET)
        else:
            print("DEBUG: Not enough perms for !changec")

    def get_description(self):
        return "!changec [channel] - Switches to that channel (leaves current)"
