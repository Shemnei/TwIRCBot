import random
import re
import threading

import time

import master


class IRCPlugin(master.Plugin):

    def get_regex(self):
        return r"(@.* )?:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :!add_cur "

    def cmd(self, line):
        args = re.sub(self.get_regex(), "", line).split()

        if len(args) < 2 and args[1].isnumeric():
            return

        amount = int(args[1])
        args.append("")
        msg = " ".join(args[2:])
        if args[0].lower() == "all":
            t = threading.Thread(target=self.bot.get_currency_manager().add_currency, args=(amount, msg), name="cmd_add_currency_thread")
            t.start()
        else:
            self.data_manager.add_user_currency(args[0].lower(), amount)
            self.connection.add_chat_msg(msg)

    def get_description(self):
        return "!add_cur [all/user] [amount] (msg) - Adds specified amount to all or specified users"
