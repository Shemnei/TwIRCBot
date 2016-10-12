import master


class IRCPlugin(master.CommandPlugin):

    COMMAND = "!x"
    ARGS = ""
    DESCRIPTION = "Plugin for simple Text responses"
    PERMISSION_LEVEL = 0
    ADD_TO_HELP = False

    COOL_DOWN = 10

    def get_regex(self):
        return r"PRIVMSG #\w+ :!(\w+)$"

    def cmd(self, message):
        if self.is_valid_request(message.user):
            name = message.msg[1:]
            if name == "youtube":
                self.connection.add_chat_msg("I am on youtube: www.youtube.com")
            elif name == "twitter":
                self.connection.add_chat_msg("I am on twitter: www.twitter.com")
