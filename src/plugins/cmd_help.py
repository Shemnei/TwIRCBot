import os
import time

import master


class IRCPlugin(master.CommandPlugin):

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
        master.Plugin.__init__(self)
        self.__plugins = None
        self.__last_used = None

    def get_regex(self):
        return r"PRIVMSG #\w+ :!help($| )"

    def cmd(self, message):
        if not self.__last_used or (time.time() - self.__last_used > IRCPlugin.COOL_DOWN):
            plugin = message.msg[6:].lower().strip()
            filer_str = "cmd_" + plugin
            out = []
            filtered = filter(lambda module: filer_str in module[1].__module__, enumerate(self.__plugins))
            if plugin:
                using = IRCPlugin.specific
            else:
                using = IRCPlugin.all

            for m in list(filtered):
                f = getattr(m[1], "get_description", using["not_implemented"])
                if isinstance(f, str):
                    out.append(f % os.path.basename(m[1].__module__))
                else:
                    if plugin:
                        tmp = f()
                    else:
                        tmp = f().split()[0]
                    out.append(tmp)
            if len(out):
                self.connection.add_chat_msg(using["msg"] + ", ".join(out))
            else:
                self.connection.add_chat_msg(using["none_found"] % plugin)

            self.__last_used = time.time()

    def on_load(self, bot):
        super().on_load(bot)
        self.__plugins = self.plugin_manager.get_loaded_plugins()

    def on_refresh(self):
        self.__plugins = self.plugin_manager.get_loaded_plugins()

    def get_description(self):
        return "!help (command) - Gives info about all loaded commands or a specific one"
