import threading

import master


class IRCPlugin(master.CommandPlugin):

    COMMAND = "!add_cur"
    ARGS = "[all/user] [amount] (msg)"
    DESCRIPTION = "Adds specified amount to all or specific users"
    PERMISSION_LEVEL = 3
    ADD_TO_HELP = True

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
