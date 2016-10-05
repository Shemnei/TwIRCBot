import re

import master


class IRCPlugin(master.Plugin):

    def get_regex(self):
        return r"(@.* )?:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :!status$"

    def cmd(self, line):
        user = re.search(r":\w+!", line).group(0).strip(":!").lower()
        db_user = self.data_manager.get_user(user)
        self.connection.add_chat_msg(".w %s Yours stats: [perm_lvl:%i / coins: %i]!" % db_user)

    def get_description(self):
        return "!status - Gives info about user"
