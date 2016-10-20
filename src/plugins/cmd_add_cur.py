import logging
import threading

import master

logger = logging.getLogger(__name__)


class IRCPlugin(master.CommandPlugin):

    COMMAND = "!add_cur"
    ARGS = "[all/user] [amount] (msg)"
    DESCRIPTION = "Adds specified amount to all or specific users"
    PERMISSION_LEVEL = 3
    ADD_TO_HELP = True

    def get_regex(self):
        return r"PRIVMSG #\w+ :!add_cur \w+ \d+"

    def cmd(self, message):
        if message.user.perm_lvl >= self.data_manager.PermissionLevel.moderator \
                or message.user.name == self.config["connection"]["nick_name"].lower()\
                or message.user.name == self.config["connection"]["channel"]:

            args = message.msg[9:].split()

            target = args[0].lower()
            amount = int(args[1])
            msg = " ".join(args[2:])
            if target == "all":
                logger.log(logging.DEBUG, "@%s - add_cur all %i" % (str(message.user), amount))
                t = threading.Thread(target=self.bot.get_currency_manager().add_currency, args=(amount, msg),
                                     name="cmd_add_currency_thread")
                t.start()
            else:
                logger.log(logging.DEBUG, "@%s -> add_cur %s %i" % (str(message.user), target, amount))
                self.data_manager.add_user_currency(target, amount)
                self.connection.add_chat_msg(msg)
