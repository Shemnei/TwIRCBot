import threading

import master


class IRCPlugin(master.CommandPlugin):

    def get_regex(self):
        return r"PRIVMSG #\w+ :!add_cur \w+ \d+"

    def cmd(self, message):
        if message.user[1] >= self.data_manager.PermissionLevel.moderator \
                or message.user[0] == self.config["connection"]["nick_name"].lower()\
                or message.user[0] == self.config["connection"]["channel"]:

            args = message.msg[9:].split()

            target = args[0].lower()
            amount = int(args[1])
            msg = " ".join(args[2:])
            if target == "all":
                t = threading.Thread(target=self.bot.get_currency_manager().add_currency, args=(amount, msg),
                                     name="cmd_add_currency_thread")
                t.start()
            else:
                self.data_manager.add_user_currency(target, amount)
                self.connection.add_chat_msg(msg)

    def get_description(self):
        return "!add_cur [all/user] [amount] (msg) - Adds specified amount to all or specific users"
