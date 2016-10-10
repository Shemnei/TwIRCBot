import master


class IRCPlugin(master.CommandPlugin):

    def get_regex(self):
        return r"PRIVMSG #\w+ :!status$"

    def cmd(self, message):
        self.connection.add_chat_msg(".w %s Yours stats: [perm_lvl:%i / coins: %i]!" % message.user)

    def get_description(self):
        return "!status - Gives info about user"
