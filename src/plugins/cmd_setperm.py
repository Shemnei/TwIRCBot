import re

import master


class IRCPlugin(master.Plugin):

    def get_regex(self):
        return r"(@.* )?:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :!setperm (\w+) (\d+)$"

    def cmd(self, line):
        match = re.search(self.get_regex(), line)
        # FIXME .group is invalid if no tags
        print("DEBUG: Set permission level of %s to %s" % (match.group(2), match.group(3)))
        self.bot.get_data_manager().set_user_permlvl(match.group(2), int(match.group(3)))

    def get_description(self):
        return "!setperm [user][level] - Sets permission level of user"