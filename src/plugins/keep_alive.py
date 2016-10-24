import logging

import master

logger = logging.getLogger(__name__)


class IRCPlugin(master.GenericPlugin):

    def get_regex(self):
        return r"^PING :"

    def cmd(self, message):
        pong_msg = message.raw_line.replace("PING", "PONG")
        self.connection.add_raw_msg(pong_msg, important=True)
        logger.log(logging.DEBUG, "PING > %s" % pong_msg)
