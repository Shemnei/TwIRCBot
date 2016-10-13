import logging

import master

logger = logging.getLogger(__name__)


class IRCPlugin(master.CommandPlugin):

    COMMAND = "!hello"
    ARGS = ""
    DESCRIPTION = "I'm a friendly bot"
    PERMISSION_LEVEL = 0
    ADD_TO_HELP = True

    COOL_DOWN = 10
    IS_COOL_DOWN_GLOBAL = True

    def get_regex(self):
        return r"PRIVMSG #\w+ :!hello$"

    def cmd(self, message):
        if self.is_valid_request(message.user):
            user = message.user[0]
            if message.tags and message.tags.get("display-name", None):
                user = message.tags["display-name"]

            logger.log(logging.DEBUG, "@%s -> hello" % str(message.user))
            self.connection.add_chat_msg("Hello there %s" % user)
