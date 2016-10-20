import logging

import master

logger = logging.getLogger(__name__)


class IRCPlugin(master.CommandPlugin):

    COMMAND = "!help"
    ARGS = "(command)"
    DESCRIPTION = "Gives info about all loaded commands or a specific one"
    PERMISSION_LEVEL = 0
    ADD_TO_HELP = True

    COOL_DOWN = 10

    all = {
        "msg": "Commands: ",
        "not_implemented": "[%s] cmd not implemented",
        "none_found": "No commands found%s"
    }
    specific = {
        "msg": "Usage: ",
        "not_implemented": "[%s] usage not implemented",
        "none_found": "No command found for %s"
    }

    def __init__(self):
        super().__init__()
        self.__plugins = None

    def get_regex(self):
        return r"PRIVMSG #\w+ :!help($| )"

    def cmd(self, message):
        if self.__plugins is None:
            self.__plugins = self.plugin_manager.get_registered_commands()
        if self.is_valid_request(message.user):
            plugin = message.msg[6:].lower().strip()
            logger.log(logging.DEBUG, "@%s -> help %s" % (str(message.user), plugin))
            filer_str = plugin
            out = []
            filtered = filter(lambda module: filer_str in module.cmd and module.add_to_help
                                             and message.user.perm_lvl >= module.perm_lvl, self.__plugins)
            if plugin:
                using = IRCPlugin.specific
            else:
                using = IRCPlugin.all

            for m in list(filtered):
                if plugin:
                    tmp = m.cmd + " " + m.args + " - " + m.description
                else:
                    tmp = m.cmd
                out.append(tmp)
            if len(out):
                self.connection.add_chat_msg(using["msg"] + ", ".join(out))
            else:
                self.connection.add_chat_msg(using["none_found"] % plugin)

    def on_refresh(self):
        self.__plugins = None
