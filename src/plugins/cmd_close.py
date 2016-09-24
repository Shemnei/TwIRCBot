import master


class IRCPlugin(master.Plugin):

    def get_regex(self):
        return r":\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :!close$"

    def cmd(self, line):
        self.connection.shutdown()

    def get_description(self):
        return "!close - Terminates bot"
