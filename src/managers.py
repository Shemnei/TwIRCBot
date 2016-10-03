import datetime
import json
import os
import threading
import time
from importlib import util
import urllib.request

import master


class PluginManager:

    def __init__(self, bot):
        self.loaded_plugins = []

        self.__config = bot.get_config_manager()
        self.__connection = bot.get_connection()
        self.__bot = bot

    def load_plugins(self):
        if not self.__config["plugins"]["load_plugins"]:
            print("DEBUG: Plugins not loaded (settings:load_plugins)")
            return

        start_load_plugins = time.time()

        path = self.__config["paths"]["plugin_dir"]
        if not os.path.isdir(path):
            os.makedirs(path)

        files = filter(lambda f: f.endswith('.py'), os.listdir(path))
        modules = []
        for file in files:
            spec = util.spec_from_file_location(file[:-3], os.path.join(self.__config["paths"]["plugin_dir"], file))
            module = util.module_from_spec(spec)
            spec.loader.exec_module(module)
            modules.append(module)

        plugins = list(map(lambda plugin: getattr(plugin, 'IRCPlugin')(), modules))
        loaded = list(filter(lambda plugin: isinstance(plugin, master.Plugin), plugins))

        # custom load order
        load_order = self.__config["plugins"]["custom_load_order"]
        if load_order:
            self.loaded_plugins = []
            tmp = [x.__module__ for x in loaded]
            for pl in load_order:
                if pl in tmp:
                    index = tmp.index(pl)
                    self.loaded_plugins.append(loaded[index])
                    loaded.pop(index)
            self.loaded_plugins.extend(loaded)
        else:
            self.loaded_plugins = list(loaded)

        # disabled plugins
        disabled_plugins = self.__config["plugins"]["disabled_plugins"]
        if disabled_plugins:
            tmp = [x.__module__ for x in self.loaded_plugins]
            for x in disabled_plugins:
                if x in tmp:
                    index = tmp.index(x)
                    print("-Plugin %s disabled !" % self.loaded_plugins[index].__module__)
                    self.loaded_plugins.pop(tmp.index(x))
                    tmp.pop(tmp.index(x))

        for p in self.loaded_plugins:
            p.on_load(self.__bot)

        not_loaded = filter(lambda plugin: not isinstance(plugin, master.Plugin), plugins)
        for p in not_loaded:
            print("-Plugin %s not loaded -> needs to be derived from master.Plugin" % p.__module__)

        print("DEBUG: Plugins Loaded in %fms" % ((time.time() - start_load_plugins)*1000))

    def close(self):
        print("DEBUG: Plugin Manager closing")

        for p in self.loaded_plugins:
            p.on_close()


class CurrencyManager:
    CHATTERS_URL = "https://tmi.twitch.tv/group/user/%s/chatters"

    # every interval gets viewers and add x currency to their account
    # "chatters" -> "moderators", "staff", "global_mods", "viewers"

    def __init__(self, bot):
        self.__bot = bot
        self.__config = bot.get_config_manager()
        self.__connection = bot.get_connection()

        self.__enabled = None
        self.__channel = None
        self.__interval = None
        self.__amount = None
        self.__message = None

        self.__running = False
        self.__stop = threading.Event()
        self.__currency_thread = None

    def load_settings(self):
        self.__enabled = self.__config["currency"]["enabled"]
        self.__channel = self.__config["currency"]["channel"]
        self.__interval = int(self.__config["currency"]["interval"]) or 300
        self.__amount = int(self.__config["currency"]["amount"]) or 1
        self.__message = self.__config["currency"]["message"]

    def reload_settings(self):
        print("DEBUG: Currency System reloading")
        self.load_settings()

        if not self.__enabled and self.__currency_thread and self.__currency_thread.is_alive():
            self.close()

        elif self.__currency_thread and not self.__currency_thread.is_alive():
            self.start()

    def start(self):
        self.__currency_thread = threading.Thread(target=self.__heartbeat_routine, name="currency_thread")
        self.__currency_thread.start()

    def __heartbeat_routine(self):
        if not self.__enabled:
            print("DEBUG: Currency System disabled")
            return
        try:
            print("DEBUG: Currency System starting")
            self.__running = True
            while not self.__stop.wait(1):
                self.__stop.wait(self.__interval)
                with urllib.request.urlopen(CurrencyManager.CHATTERS_URL % self.__channel) as c:
                    content = c.read()
                jo = json.loads(content.decode())
                chatters = []
                [chatters.extend(x) for x in jo["chatters"].values()]
                # process chatters

                # end
                print("\033[34;1m{" + datetime.datetime.now().strftime("%H:%M:%S") +
                      "} Currency given to %s viewers\033[0m" % jo["chatter_count"])
                self.__connection.add_raw_msg("PRIVMSG #%s :%s" % (self.__channel, self.__message))
        finally:
            self.__running = False

    def close(self):
        # TODO add safety so that it doesnt get shutdown during adding
        print("DEBUG: Currency System closing")
        self.__stop.set()
        self.__currency_thread.join()


class ConfigManager:
    pass