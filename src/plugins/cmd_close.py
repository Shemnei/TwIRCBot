import logging

import master

logger = logging.getLogger(__name__)


class IRCPlugin(master.CommandPlugin):

    COMMAND = "!close"
    ARGS = ""
    DESCRIPTION = "Closes bot"
    PERMISSION_LEVEL = 4
    ADD_TO_HELP = False

    def get_regex(self):
        return r"PRIVMSG #\w+ :!close$"

    def cmd(self, message):
        if message.user[0] == self.config["connection"]["nick_name"].lower()\
                or message.user[0] == self.config["connection"]["channel"].lower():
            logger.log(logging.DEBUG, "@%s -> close" % str(message.user))
            self.bot.stop()
