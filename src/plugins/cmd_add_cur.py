import re
import threading

import master


class IRCPlugin(master.Plugin):

    def get_regex(self):
        return r"(@.* )?:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :!add_cur \w+ \d+"

    def cmd(self, line):
        user = re.search(r":\w+!", line).group(0).strip(":!").lower()
        if self.data_manager.get_user_permlvl(user) >= self.data_manager.PermissionLevel.moderator:

            args = re.sub(r"(@.* )?:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :!add_cur ", "", line).split()

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
