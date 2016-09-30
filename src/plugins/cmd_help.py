import os
import re

import master


class IRCPlugin(master.Plugin):

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
        self.plugins = None

    def get_regex(self):
        return r"(@.* )?:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :!help"

    def cmd(self, line):
        plugin = re.sub(self.get_regex(), "", line).strip()
        filer_str = "cmd_" + plugin
        out = []
        filtered = filter(lambda module: filer_str in module[1].__module__, enumerate(self.plugins))
        if plugin:  # not empty
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

    def on_load(self, bot):
        super().on_load(bot)
        self.plugins = self.plugin_manager.loaded_plugins

    def on_refresh(self):
        self.plugins = self.plugin_manager.loaded_plugins

    def get_description(self):
        return "!help (command) - Gives info about all loaded commands or a specific one"
