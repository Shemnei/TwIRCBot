import collections
import datetime
import enum
import json
import logging
import math
import os
import queue
import re
import sqlite3
import sys
import threading
import time
import urllib.request
from importlib import util

import master

logger = logging.getLogger(__name__)


class PluginManager:

    Command = collections.namedtuple("Command", ["cmd", "args", "description", "perm_lvl", "add_to_help"])
    Filter = collections.namedtuple("Filter", ["filter", "description", "perm_lvl"])

    def __init__(self, bot):
        self.__loaded_plugins = []
        self.__registered_commands = []
        self.__registered_filters = []

        self.__config = bot.get_config_manager()
        self.__connection = bot.get_connection()
        self.__bot = bot

    def load_plugins(self):
        if not self.__config.config["plugins"]["load_plugins"]:
            logger.log(logging.INFO, "Plugins not loaded (settings:load_plugins)")
            return

        start_load_plugins = time.time()

        path = self.__config.config["paths"]["plugin_dir"]
        if not os.path.isdir(path):
            os.makedirs(path)

        files = filter(lambda f: f.endswith('.py'), os.listdir(path))
        modules = []
        for file in files:
            spec = util.spec_from_file_location(file[:-3], os.path.join(self.__config.config["paths"]["plugin_dir"], file))
            module = util.module_from_spec(spec)
            spec.loader.exec_module(module)
            modules.append(module)

        plugins = list(map(lambda plugin: getattr(plugin, 'IRCPlugin')(), modules))
        loaded = list(filter(lambda plugin: isinstance(plugin, master.Plugin), plugins))

        # custom load order
        load_order = self.__config.config["plugins"]["custom_load_order"]
        if load_order:
            self.__loaded_plugins = []
            tmp = [x.__module__ for x in loaded]
            for pl in load_order:
                if pl in tmp:
                    index = tmp.index(pl)
                    self.__loaded_plugins.append(loaded[index])
                    loaded.pop(index)
            self.__loaded_plugins.extend(loaded)
        else:
            self.__loaded_plugins = list(loaded)

        # disabled plugins
        disabled_plugins = self.__config.config["plugins"]["disabled_plugins"]
        if disabled_plugins:
            tmp = [x.__module__ for x in self.__loaded_plugins]
            for x in disabled_plugins:
                if x in tmp:
                    index = tmp.index(x)
                    logger.log(logging.INFO, "-Plugin %s disabled !" % self.__loaded_plugins[index].__module__)
                    self.__loaded_plugins.pop(tmp.index(x))
                    tmp.pop(tmp.index(x))

        for p in self.__loaded_plugins:
            p.on_load(self.__bot)

        not_loaded = filter(lambda plugin: not isinstance(plugin, master.Plugin), plugins)
        for p in not_loaded:
            logger.log(logging.WARNING, "-Plugin %s not loaded -> needs to be derived from master.Plugin" % p.__module__)

        logger.log(logging.DEBUG, "Plugins Loaded in %fms" % ((time.time() - start_load_plugins) * 1000))

    def register_command(self, cmd, args, description, perm_lvl=0, add_to_help=True):
        cmds = [x.cmd for x in self.__registered_commands]
        if cmd not in cmds:
            self.__registered_commands.append(self.Command(cmd, args, description, perm_lvl, add_to_help))

    def register_filter(self, filter, description, perm_lvl=0):
        filters = [x.filter for x in self.__registered_filters]
        if filter not in filters:
            self.__registered_filters.append(self.Filter(filter, description, perm_lvl))

    def handle_channel_change(self, channel):
        for p in self.__loaded_plugins:
            p.on_channel_change(channel)

    def get_registered_commands(self):
        return self.__registered_commands[:]

    def get_registered_filters(self):
        return self.__registered_filters[:]

    def get_loaded_plugins(self):
        return self.__loaded_plugins[:]

    def close(self):
        logger.log(logging.INFO, "Plugin Manager closing")

        for p in self.__loaded_plugins:
            p.on_close()


class MessageDistributor:

    Message = collections.namedtuple("Message", ["user", "tags", "cmd", "channel", "msg", "raw_line"])

    def __init__(self, bot):
        self.__running = False

        self.__bot = bot
        self.__data_manager = bot.get_data_manager()
        self.__config = bot.get_config_manager()

        self.__loaded_plugins = None

        self.__distribution_queue = queue.Queue()
        self.__distribution_thread = threading.Thread(target=self.__distribution_routine, name="distribution_thread")

    def get_active_plugins(self):
        self.__loaded_plugins = self.__bot.get_plugin_manager().get_loaded_plugins()

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
            user = DataManager.User(user_name, 0, 0)
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
                    for p in self.__loaded_plugins:
                        if re.search(p.get_regex(), line):
                            p.cmd(message)
            except queue.Empty:
                pass
            except KeyboardInterrupt:
                raise

    def start(self):
        logger.log(logging.INFO, "Distributor starting")

        self.__running = True
        self.__loaded_plugins = self.__bot.get_plugin_manager().get_loaded_plugins()
        self.__distribution_thread.start()

    def close(self):
        logger.log(logging.INFO, "Distributor closing")
        self.__running = False
        self.__distribution_thread.join()


class HeartbeatManager(master.Observable):

    CHATTERS_URL = "https://tmi.twitch.tv/group/user/%s/chatters"

    # "chatters" -> "moderators", "staff", "global_mods", "viewers"
    def __init__(self, bot):
        super().__init__()

        self.__bot = bot
        self.__config = bot.get_config_manager()

        self.__chatter_count = None
        self.__stored_chatters = {}
        self.__last_updated = None

        self.__channel = None
        self.__interval = None

        self.__heartbeat_thread = None
        self.__stop = threading.Event()

    def load_settings(self):
        self.__channel = self.__config.config["connection"]["channel"]
        if self.__config.config["currency"]["enabled"]:
            self.__interval = int(self.__config.config["currency"]["interval"]) or 300
        else:
            self.__interval = 300

    def reload_settings(self):
        logger.log(logging.INFO, "Heartbeat System reloading")
        self.load_settings()

        if self.__heartbeat_thread and self.__heartbeat_thread.is_alive():
            self.close()

        elif self.__heartbeat_thread and not self.__heartbeat_thread.is_alive():
            self.start()

    def start(self):
        self.__heartbeat_thread = threading.Thread(target=self.__heartbeat_routine, name="heartbeat_thread")
        self.__heartbeat_thread.start()

    def __heartbeat_routine(self):
        try:
            logger.log(logging.INFO, "Heartbeat System starting")
            self.__running = True
            while not self.__stop.wait(1):
                data = urllib.request.urlopen(self.CHATTERS_URL % self.__channel).read()
                json_obj = json.loads(data.decode())

                self.__last_updated = time.time()
                self.__chatter_count = json_obj["chatter_count"]
                self.__stored_chatters = json_obj["chatters"]

                self.notify_observers("chatters")

                self.__stop.wait(self.__interval)

        finally:
            self.__running = False

    def get_chatters_list(self):
        return self.__stored_chatters.copy()

    def get_chatters_amount(self):
        return self.__chatter_count

    def close(self):
        logger.log(logging.INFO, "Heartbeat System closing")
        self.__stop.set()
        self.__heartbeat_thread.join()


class CurrencyManager(master.Observer):

    def __init__(self, bot):
        self.__bot = bot
        self.__config = bot.get_config_manager()
        self.__connection = bot.get_connection()
        self.__data_manager = bot.get_data_manager()

        self.__enabled = None
        self.__interval = None
        self.__amount = None
        self.__message = None
        self.__chatters = {}

    def load_settings(self):
        self.__enabled = self.__config.config["currency"]["enabled"]
        self.__interval = int(self.__config.config["currency"]["interval"]) or 300
        self.__amount = int(self.__config.config["currency"]["amount"]) or 1
        self.__message = self.__config.config["currency"]["message"]

    def reload_settings(self):
        logger.log(logging.INFO, "Currency System reloading")
        self.load_settings()

    def update(self, observable, args):
        if args == "chatters":
            self.__chatters = observable.get_chatters_list()
            if self.__enabled and self.__amount != 0:
                threading.Thread(target=self.add_currency, args=(self.__amount, self.__message),
                                 name="currency_thread").start()

    def add_currency(self, currency_amount, msg):
        start = time.clock()

        chatters = []
        [chatters.extend(x) for x in self.__chatters.values()]

        self.__data_manager.process_chatters_list(chatters, currency_amount)

        logger.log(logging.DEBUG, "Currency add time: %fms" % ((time.clock() - start) * 1000))
        logger.log(logging.INFO, "Currency added to %s chatters" % len(chatters))

        print("\033[34;1m{" + datetime.datetime.now().strftime("%H:%M:%S") +
              "} Currency given to %s viewers\033[0m" % len(chatters))
        self.__connection.add_chat_msg(msg)

    def close(self):
        logger.log(logging.INFO, "Currency System closing")
        self.__bot.get_heartbeat_manager().remove_observer(self)


class CronManager:

    CronJob = collections.namedtuple("CronJob", ["interval", "channel", "message", "ignore_silent_mode"])

    def __init__(self, bot):
        super().__init__()

        self.__config = bot.get_config_manager()
        self.__connection = bot.get_connection()

        self.__max_sleep_time = None
        self.__cron_jobs = None
        self.__loaded_cron_cfg = None
        self.__running = False
        self.__cron_thread = None

        self.stop = threading.Event()

    def load_cron_jobs(self):
        self.__cron_jobs = []
        self.__max_sleep_time = None

        intervals = []
        for job in self.__config.config["cron"].values():
            if job["enabled"]:
                self.__cron_jobs.append(self.CronJob(job["interval"],
                                                     job["channel"],
                                                     job["message"],
                                                     job.get("ignore_silent_mode", False)))
                intervals.append(job["interval"])
        self.__cron_jobs.sort(key=lambda x: x.interval)

        smallest_interval = 0
        for i in intervals:
            if smallest_interval is None:
                smallest_interval = i
            else:
                smallest_interval = math.gcd(smallest_interval, i)

        self.__max_sleep_time = smallest_interval
        logger.log(logging.DEBUG, "Cron sleep time set to %is" % self.__max_sleep_time)

    def reload_jobs(self):
        logger.log(logging.INFO, "Cron jobs reloading")
        self.load_cron_jobs()
        if self.__cron_thread and not self.__cron_thread.is_alive():
            self.start()

    def start(self):
        logger.log(logging.INFO, "Cron starting")
        self.__cron_thread = threading.Thread(target=self.__cron_routine, name="cron_thread")
        self.__cron_thread.start()

    def __cron_routine(self):
        if not self.__cron_jobs or len(self.__cron_jobs) == 0:
            logger.log(logging.INFO, "Cron stopped [no jobs]")
            return
        time_slept = 0
        try:
            self.__running = True
            while not self.stop.wait(1):
                self.stop.wait(self.__max_sleep_time)
                time_slept += self.__max_sleep_time
                for cj in self.__cron_jobs:
                    if float(time_slept/cj.interval).is_integer():
                        self.__connection.add_raw_msg("PRIVMSG #%s :%s" % (cj.channel, cj.message),
                                                      cj.ignore_silent_mode)

                        print("\033[34;1m{" + datetime.datetime.now().strftime("%H:%M:%S")
                              + "} Cron job executed [%s/%i]\033[0m" % (cj.channel, cj.interval))
                        logging.log(logging.DEBUG, "Cron job executed [%s/%i]" % (cj.channel, cj.interval))

                if self.__cron_jobs[-1].interval <= time_slept:
                    time_slept = 0
        finally:
                self.__running = False

    def close(self):
        logging.log(logging.INFO, "Cron closing")
        self.stop.set()
        self.__cron_thread.join()


class DataManager:
    DATABASE_NAME = "users.db"

    User = collections.namedtuple("User", ["name", "perm_lvl", "currency"])

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
        self.__channel = self.__config.config["connection"]["channel"]
        self.__loaded_user = None

    def setup_database(self):
        start = time.clock()
        con = sqlite3.connect(DataManager.DATABASE_NAME)
        cur = con.cursor()

        cur.execute("CREATE TABLE IF NOT EXISTS " + self.__channel
                    + " (id VARCHAR NOT NULL, perm_lvl INTEGER, currency INTEGER, PRIMARY KEY (id))")
        con.commit()

        con.close()
        logging.log(logging.DEBUG, "Database setup time: %fms" % ((time.clock() - start) * 1000))

    def process_chatters_list(self, chatters, currency_amount):
        con = sqlite3.connect(DataManager.DATABASE_NAME, timeout=10)
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
        con = sqlite3.connect(DataManager.DATABASE_NAME, timeout=10)
        cur = con.cursor()
        try:
            cur.execute("INSERT INTO " + self.__channel + " (id, perm_lvl, currency) VALUES (?,?,?)",
                        (user, perm_lvl, currency))
            self.__loaded_user = (user, perm_lvl, currency)
            con.commit()
        finally:
            con.close()

    def get_user_currency(self, user):
        return self.get_user(user).currency

    def set_user_currency(self, user, new_currency):
        con = sqlite3.connect(DataManager.DATABASE_NAME, timeout=10)
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
        con = sqlite3.connect(DataManager.DATABASE_NAME, timeout=10)
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
        return self.get_user(user).perm_lvl

    def set_user_permlvl(self, user, new_permlvl):
        con = sqlite3.connect(DataManager.DATABASE_NAME, timeout=10)
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
        con = sqlite3.connect(DataManager.DATABASE_NAME, timeout=10)
        cur = con.cursor()

        cur.execute("INSERT OR IGNORE INTO " + self.__channel + " (id, perm_lvl, currency) VALUES (?,?,?)",
                    (user, 0, 0))
        cur.execute("SELECT * FROM " + self.__channel + " WHERE id=?", (user,))
        user = cur.fetchone()
        con.commit()
        con.close()

        user = self.User(*user)
        self.__loaded_user = user
        return user

    def close(self):
        logging.log(logging.INFO, "DEBUG: Data System closing")


class ConfigManager:
    DEFAULT_VALUES = {
        "paths": {
            "plugin_dir": "plugins",
            "log_dir": "logs"
        },
        "connection": {
            "server": "irc.chat.twitch.tv",
            "port": 443,
            "ssl": True,
            "nick_name": "user_name",
            "oauth_token": "oauth_token",
            "client_id": "client_id",
            "channel": "your_channel",
            "msg_decoding": "utf-8",
            "msg_encoding": "utf-8",
            "timeout_between_msg": 0.7,
            "receive_size_bytes": 4096,
            "auto_reconnect": True,
            "membership_messages": True,
            "tags": True,
            "commands": True
        },
        "logging": {
            "max_log_files": 5,
            "enable_console_logging": True,
            "console_log_level": 20,
            "enable_file_logging": True,
            "file_log_level": 10,
            "log_format": "[%(asctime)s / %(name)s / %(levelname)s] %(message)s"
        },
        "general": {
            "join_msg": ".me up and running!",
            "depart_msg": ".me battery empty, leaving!",
            "silent_mode": True,
            "only_silent_in_other_channels": True
        },
        "plugins": {
            "load_plugins": True,
            "custom_load_order": ["gui"],
            "disabled_plugins": ["print_raw", "print_messages"]
        },
        "plugin_settings": {
            "lang_t2s": "en",
            "enable_gui_messages": True,
            "enable_gui_emotes": True,
            "enable_gui_badges": True
        },
        "currency": {
            "enabled": False,
            "interval": 300,
            "amount": 1,
            "message": "I'm laughing straight to the bank with this (Ha, ha ha ha ha ha, ha, ha ha ha ha ha)"
        },
        "cron": {
            "cron_job_one": {
                "enabled": False,
                "channel": "own_channel",
                "interval": 10,
                "message": "Hello i am cron job one"
            },
            "cron_job_two": {
                "enabled": False,
                "ignore_silent_mode": False,
                "channel": "own_channel",
                "interval": 30,
                "message": "Hello i am cron job two"
            }
        }
    }

    FILE_NAME = "config.json"

    def __init__(self, bot, encoding="utf-8"):
        self.bot = bot
        self.__encoding = encoding
        self.config = None

    def load_cfg(self):
        if not os.path.isfile(self.FILE_NAME):
            with open(self.FILE_NAME, "w") as file:
                json.dump(self.DEFAULT_VALUES, file, indent=4)
            print("No config found - created one")
            print("Edit config - then start again")
            sys.exit()

        with open(self.FILE_NAME) as content:
            try:
                self.config = json.load(content, encoding=self.__encoding)
            except Exception as e:
                print("Invalid Json Format: %s" % e)
                sys.exit()



