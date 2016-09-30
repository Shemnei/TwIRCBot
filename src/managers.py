import os
import time
from importlib import util

import master


class PluginManager:

    def __init__(self, bot):
        self.loaded_plugins = None

        self.__config = bot.get_config_manager()
        self.__connection = bot.get_connection()
        self.__bot = bot

    def load_plugins(self):
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
        loaded = filter(lambda plugin: isinstance(plugin, master.Plugin), plugins)
        self.loaded_plugins = list(loaded)
        not_loaded = filter(lambda plugin: not isinstance(plugin, master.Plugin), plugins)
        for p in not_loaded:
            print("DEBUG: %s not loaded -> needs to be derived from master.Plugin" % p.__module__)

        for p in self.loaded_plugins:
            p.on_load(self.__bot)

        print("DEBUG: Plugins Loaded in %fms" % ((time.time() - start_load_plugins)*1000))

    def close(self):
        print("DEBUG: Plugin Manager closing")

        for p in self.loaded_plugins:
            p.on_close()



class ConfigManager:
    pass