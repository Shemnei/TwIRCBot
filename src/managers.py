import datetime
import enum
import json
import os
import queue
import sqlite3
import threading
import time
import urllib.request
from importlib import util
import collections

import re

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

        print("DEBUG: Plugins Loaded in %fms" % ((time.time() - start_load_plugins) * 1000))

    def close(self):
        print("DEBUG: Plugin Manager closing")

        for p in self.loaded_plugins:
            p.on_close()


class MessageDistributor:

    Message = collections.namedtuple("Message", ["user", "tags", "cmd", "channel", "msg", "raw_line"])

    def __init__(self, bot):
        self.__running = False

        self.__bot = bot
        self.__data_manager = bot.get_data_manager()

        self.__distribution_queue = queue.Queue()
        self.__distribution_thread = threading.Thread(target=self.__distribution_routine, name="distribution_thread")

    def add_line(self, msg):
        try:
            self.__distribution_queue.put_nowait(msg)
        except queue.Full():
            pass

    @staticmethod
    def parse_tags(tag_str):
        tag_str = tag_str.strip()
        tag_str = tag_str.lstrip('@')
        tags = {}
        for tag_c in tag_str.split(";"):
            i = tag_c.find("=")
            tags[tag_c[:i]] = tag_c[i + 1:]
        return tags

    def parse_line(self, line):
        # (User, tags, cmd, msg)
        tags = None
        channel = None
        msg = None

        parts = line.split()
        offset = 0

        if line.startswith('@'):
            tags = self.parse_tags(parts[0])
            offset = True

        index = parts[0 + offset].find('!')
        if index == -1:
            user_name = parts[0 + offset]
        else:
            user_name = parts[0 + offset][1:index]
        if user_name.startswith(':'):
            user = (user_name, 0, 0)
        else:
            user = self.__data_manager.get_user(user_name)

        cmd = parts[1 + offset]

        if len(parts) >= (3 + offset):
            channel = parts[2 + offset].replace('#', '')

        if len(parts) >= (4 + offset):
            msg = " ".join(parts[3 + offset:]).lstrip(':')

        return MessageDistributor.Message(user, tags, cmd, channel, msg, line)

    def __distribution_routine(self):
        while self.__running:
            try:
                line = self.__distribution_queue.get(timeout=5)
                if line:
                    message = self.parse_line(line)
                    for p in self.__bot.get_plugin_manager().loaded_plugins:
                        if re.match(p.get_regex(), line):
                            p.cmd(message)
            except queue.Empty:
                pass
            except KeyboardInterrupt:
                raise

    def start(self):
        print("DEBUG: Distributor starting")
        self.__running = True
        self.__distribution_thread.start()

    def close(self):
        print("DEBUG: Distributor closing")
        self.__running = False
        self.__distribution_thread.join()


class CurrencyManager:
    CHATTERS_URL = "https://tmi.twitch.tv/group/user/%s/chatters"

    # every interval gets viewers and add x currency to their account
    # "chatters" -> "moderators", "staff", "global_mods", "viewers"

    def __init__(self, bot):
        self.__bot = bot
        self.__config = bot.get_config_manager()
        self.__connection = bot.get_connection()
        self.__data_manager = bot.get_data_manager()

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
        self.__channel = self.__config["connection"]["channel"]
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
                self.add_currency(self.__amount, self.__message)
        finally:
            self.__running = False

    def add_currency(self, currency_amount, msg):
        with urllib.request.urlopen(CurrencyManager.CHATTERS_URL % self.__channel) as c:
            content = c.read()
        jo = json.loads(content.decode())
        chatters = []
        [chatters.extend(x) for x in jo["chatters"].values()]

        # process viewer lists
        start = time.clock()

        self.__data_manager.process_chatters_list(chatters, currency_amount)

        print("Debug: Currency add time: %fms" % ((time.clock() - start) * 1000))

        # end
        print("\033[34;1m{" + datetime.datetime.now().strftime("%H:%M:%S") +
              "} Currency given to %s viewers\033[0m" % jo["chatter_count"])
        self.__connection.add_raw_msg("PRIVMSG #%s :%s" % (self.__channel, msg))

    def close(self):
        # TODO add safety so that it doesnt get shutdown during adding
        print("DEBUG: Currency System closing")
        self.__stop.set()
        self.__currency_thread.join()


class DataManager:
    DATABASE_NAME = "../users.db"

    @enum.unique
    class PermissionLevel(enum.IntEnum):
        basic = 0
        follower = 1
        subscriber = 2
        moderator = 3
        broadcaster = 4

    def __init__(self, bot):
        self.__bot = bot
        self.__config = bot.get_config_manager()
        self.__channel = self.__config["connection"]["channel"]
        self.__loaded_user = None

    def setup_database(self):
        start = time.clock()
        con = sqlite3.connect(DataManager.DATABASE_NAME)
        cur = con.cursor()

        cur.execute("CREATE TABLE IF NOT EXISTS " + self.__channel + " (id VARCHAR NOT NULL, perm_lvl INTEGER, currency INTEGER, PRIMARY KEY (id))")
        con.commit()

        con.close()
        print("Debug: Database setup time: %fms" % ((time.clock() - start) * 1000))

    def process_chatters_list(self, chatters, currency_amount):
        con = sqlite3.connect(DataManager.DATABASE_NAME)
        cur = con.cursor()

        self.__loaded_user = None

        cur.execute("BEGIN TRANSACTION")
        for user in chatters:
            cur.execute("INSERT OR REPLACE INTO " + self.__channel + " (id, perm_lvl, currency) VALUES ("
                        "?,"
                        "COALESCE((SELECT perm_lvl FROM " + self.__channel + " WHERE id=?), 0),"
                        "COALESCE((SELECT currency FROM " + self.__channel + " WHERE id=?)+?, ?))",
                        (user, user, user, currency_amount, currency_amount))
        con.commit()
        con.close()

    def add_user(self, user, perm_lvl=0, currency=0):
        con = sqlite3.connect(DataManager.DATABASE_NAME)
        cur = con.cursor()
        try:
            cur.execute("INSERT INTO " + self.__channel + " (id, perm_lvl, currency) VALUES (?,?,?)", (user, perm_lvl, currency))
            self.__loaded_user = (user, perm_lvl, currency)
            con.commit()
        finally:
            con.close()

    def get_user_currency(self, user):
        return self.get_user(user)[2]

    def set_user_currency(self, user, new_currency):
        con = sqlite3.connect(DataManager.DATABASE_NAME)
        cur = con.cursor()

        self.__loaded_user = None

        cur.execute("INSERT OR REPLACE INTO " + self.__channel + " (id, perm_lvl, currency) VALUES ("
                    "?,"
                    "COALESCE((SELECT perm_lvl FROM " + self.__channel + " WHERE id=?), 0),"
                    "?)",
                    (user, user, new_currency))
        con.commit()
        con.close()

    def add_user_currency(self, user, amount):
        con = sqlite3.connect(DataManager.DATABASE_NAME)
        cur = con.cursor()

        self.__loaded_user = None

        cur.execute("INSERT OR REPLACE INTO " + self.__channel + " (id, perm_lvl, currency) VALUES ("
                    "?,"
                    "COALESCE((SELECT perm_lvl FROM " + self.__channel + " WHERE id=?), 0),"
                    "COALESCE((SELECT currency FROM " + self.__channel + " WHERE id=?)+?, ?))",
                    (user, user, user, amount, amount))
        con.commit()
        con.close()

    def get_user_permlvl(self, user):
        return self.get_user(user)[1]

    def set_user_permlvl(self, user, new_permlvl):
        con = sqlite3.connect(DataManager.DATABASE_NAME)
        cur = con.cursor()

        self.__loaded_user = None

        cur.execute("INSERT OR REPLACE INTO " + self.__channel + " (id, perm_lvl, currency) VALUES ("
                    "?,"
                    "?,"
                    "COALESCE((SELECT currency FROM " + self.__channel + " WHERE id=?), 0))",
                    (user, new_permlvl, user))
        con.commit()
        con.close()

    def get_user(self, user):
        if self.__loaded_user and self.__loaded_user[0] == user:
            return self.__loaded_user
        con = sqlite3.connect(DataManager.DATABASE_NAME)
        cur = con.cursor()

        cur.execute("INSERT OR IGNORE INTO " + self.__channel + " (id, perm_lvl, currency) VALUES (?,?,?)", (user, 0, 0))
        cur.execute("SELECT * FROM " + self.__channel + " WHERE id=?", (user,))
        user = cur.fetchone()
        con.commit()
        con.close()

        self.__loaded_user = user
        return user

    def close(self):
        print("DEBUG: Data System closing")


class ConfigManager:
    pass
