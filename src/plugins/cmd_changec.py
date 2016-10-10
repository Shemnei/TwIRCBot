import re

import master


class IRCPlugin(master.CommandPlugin):

    def get_regex(self):
        return r"PRIVMSG #\w+ :!changec \w+$"

    def cmd(self, message):
        if message.user[0] == self.config["connection"]["nick_name"].lower():

            channel = message.msg[9:].lower().strip()
            print(self.connection.Color.GREEN + "DEBUG: CHANGING CHANNELS" + self.connection.Color.RESET)
            self.connection.join_channel(channel)

        else:
            print("DEBUG: Not enough perms for !changec")

    def get_description(self):
        return "!changec [channel] - Switches to that channel (leaves current)"
