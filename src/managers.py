import os
import time
from importlib import util

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



class ConfigManager:
    pass