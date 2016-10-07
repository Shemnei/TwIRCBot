import re

import master


class IRCPlugin(master.CommandPlugin):

    def get_regex(self):
        return r"(@.* )?:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :!setperm \w+ \d+$"

    def cmd(self, message):
        if message.user[0] == self.config["connection"]["nick_name"].lower() or user == self.config["connection"]["channel"].lower():

            args = message.msg.replace("!setperm ", '').split()
            print("DEBUG: Set permission level of %s to %s" % (args[0], args[1]))
            self.bot.get_data_manager().set_user_permlvl(args[0], int(args[1]))

    def get_description(self):
        return "!setperm [user][level] - Sets permission level of user"