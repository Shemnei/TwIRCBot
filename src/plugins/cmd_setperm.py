import re

import master


class IRCPlugin(master.Plugin):

    def get_regex(self):
        return r"(@.* )?:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :!setperm \w+ \d+$"

    def cmd(self, line):
        user = re.search(r":\w+!", line).group(0).strip(":!").lower()
        if user == self.config["connection"]["nick_name"].lower() or user == self.config["connection"]["channel"].lower():

            match = re.sub(r"(@.* )?:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :!setperm ", "", line)
            args = match.split()
            print("DEBUG: Set permission level of %s to %s" % (args[0], args[1]))
            self.bot.get_data_manager().set_user_permlvl(args[0], int(args[1]))

    def get_description(self):
        return "!setperm [user][level] - Sets permission level of user"