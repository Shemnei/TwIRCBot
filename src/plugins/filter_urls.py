import logging
import re

import master

logger = logging.getLogger(__name__)


class IRCPlugin(master.FilterPlugin):

    FILTER = "url_filter"
    DESCRIPTION = "Filters urls and ip addresses"
    PERMISSION_LEVEL = 3

    url_regex = [r"[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)",
                 r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"]
    message = "Links are not permitted %s => timeout"
    command = ".timeout %s 60 No urls permitted!"

    def get_regex(self):
        return r"PRIVMSG #\w+ :"

    def cmd(self, message):

        for regex in IRCPlugin.url_regex:
            match = re.search(regex, message.msg)
            if match is not None:
                logger.log(logging.DEBUG, "%s - %s" % (match, message.user))
                self.connection.add_chat_msg(IRCPlugin.message % message.user.name)
                self.connection.add_chat_msg(IRCPlugin.command % message.user.name)
                return
