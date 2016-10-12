import master


class IRCPlugin(master.CommandPlugin):

    COMMAND = "!status"
    ARGS = ""
    DESCRIPTION = "Gives info about user"
    PERMISSION_LEVEL = 0
    ADD_TO_HELP = True

    COOL_DOWN = 10

    def get_regex(self):
        return r"PRIVMSG #\w+ :!status$"

    def cmd(self, message):
        if self.is_valid_request(message.user):
            self.connection.add_chat_msg(".w %s Yours stats: [perm_lvl:%i / coins: %i]!" % message.user)

    def get_description(self):
        return "!status - Gives info about user"
