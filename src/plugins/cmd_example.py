import master


class IRCPlugin(master.Plugin):

    def get_regex(self):
        return r"(@.* )?:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :!ping"

    def cmd(self, line):
        self.connection.add_chat_msg("PONG")

    def on_load(self, connection):
        super().on_load(connection)
        print("EXAMPLE LOADED")

    def on_refresh(self):
        print("Custom Refresh")

    def on_close(self):
        print("Example SHUTDOWN [%s]" % self.__module__)

    def get_description(self):
        return "!example - needs space between cmd and description for help to work"