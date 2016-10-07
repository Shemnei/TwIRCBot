import re

import master


class IRCPlugin(master.Plugin):
    url_regex = [r"(https?://)?(www\.)?.+\.\w{2,6}",
                 r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"]
    message = "Links are not permitted %s => timeout"
    command = ".timeout %s 60 No urls permitted!"

    def get_regex(self):
        return r"(@.* )?:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :"

    def cmd(self, message):

        for regex in IRCPlugin.url_regex:
            match = re.search(regex, message.msg)
            if match is not None:
                print(match, end=" ")
                print(message.user)
                self.connection.add_chat_msg(IRCPlugin.message % message.user)
                self.connection.add_chat_msg(IRCPlugin.command % message.user)
                return
