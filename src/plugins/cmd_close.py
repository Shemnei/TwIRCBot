import logging

import master

logger = logging.getLogger(__name__)


class IRCPlugin(master.CommandPlugin):

    COMMAND = "!close"
    ARGS = ""
    DESCRIPTION = "Closes bot"
    PERMISSION_LEVEL = 999
    ADD_TO_HELP = False

    COOL_DOWN = 0
    IS_COOL_DOWN_GLOBAL = True

    def get_regex(self):
        return r"PRIVMSG #\w+ :!close$"

    def cmd(self, message):
        if self.is_valid_request(message.user):
            logger.log(logging.DEBUG, "@%s -> close" % str(message.user))
            self.bot.stop()
