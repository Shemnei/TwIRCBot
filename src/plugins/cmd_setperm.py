import logging

import master

logger = logging.getLogger(__name__)


class IRCPlugin(master.CommandPlugin):

    COMMAND = "!setperm"
    ARGS = "[user][level]"
    DESCRIPTION = "Sets permission level of user"
    PERMISSION_LEVEL = 4
    ADD_TO_HELP = False

    def get_regex(self):
        return r"PRIVMSG #\w+ :!setperm \w+ \d+$"

    def cmd(self, message):
        if message.user[0] == self.config["connection"]["nick_name"].lower() \
                or message.user[0] == self.config["connection"]["channel"].lower():

            args = message.msg[9:].split()
            logger.log(logging.DEBUG, "@%s -> setperm %s %s" % (message.user[0], args[0], args[1]))
            self.bot.get_data_manager().set_user_permlvl(args[0], int(args[1]))
