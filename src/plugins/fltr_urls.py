import re

import master


class IRCPlugin(master.Plugin):
    url_regex = [r"((([A-Za-z]{3,9}:(?:\/\/)?)(?:[-;:&=\+\$,\w]+@)?[A-Za-z0-9.-]+|(?:www.|[-;:&=\+\$,\w]+@)[A-Za-z0-9.-]+)((?:\/[\+~%\/.\w_]*)?\??(?:[-\+=&;%@.\w_]*)#?(?:[.\!\/\\w]*))?)",
                 r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"]
    message = "Links are not permitted %s => timeout"
    command = ".timeout %s 60"

    def get_regex(self):
        return r"(@.* )?:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :"

    def cmd(self, line):
        user = re.search(r":\w+!", line)
        user = user.group(0).strip(":!").title()

        line = re.sub(self.get_regex(), "", line)

        for regex in IRCPlugin.url_regex:
            match = re.search(regex, line)
            if match is not None:
                print(match, end=" ")
                print(user)
                self.connection.add_chat_msg(IRCPlugin.message % user)
                self.connection.add_chat_msg(IRCPlugin.command % user)
                return
