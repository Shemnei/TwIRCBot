import ctypes
import datetime
import logging
import os
import platform
import sys
import time
from logging import handlers

import connection
import managers


class Bot:

    def enable_cmd_colors(self):
        # Windows 10 build 10586: Added support to ANSI colors, enabled by default
        # Windows 10 build 14393: ANSI colors are still supported, but not default
        plt = platform.platform().split(".")
        if plt[0] == "Windows-10" and int(plt[2]) >= 14393:
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            self.__logger.log(logging.DEBUG, "Ansi escape sequence enabled [%s]" % platform.platform())

    def __setup_logging(self):
        log_dir = self.__config_manager.config["paths"]["log_dir"]
        if not os.path.isdir(log_dir):
            os.makedirs(log_dir)
        else:
            old_log_files = os.listdir(log_dir)
            difference = len(old_log_files) - int(self.__config_manager.config["logging"]["max_log_files"])
            for i in range(difference):
                try:
                    os.remove(os.path.join(log_dir, old_log_files[i]))
                    print("Removed old log file: %s" % old_log_files[i])
                except:
                    print("Could not remove old log file: %s" % old_log_files[i])

        active_handlers = []

        console_handler = logging.StreamHandler()
        if self.__config_manager.config["logging"]["enable_console_logging"]:
            console_handler.setLevel(self.__config_manager.config["logging"]["console_log_level"])
        else:
            console_handler.setLevel(sys.maxsize)
        active_handlers.append(console_handler)

        if self.__config_manager.config["logging"]["enable_file_logging"]:
            file_handler = logging.handlers.RotatingFileHandler(
                os.path.join("logs", datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + "_botlog.txt"),
                encoding="utf-8")
            file_handler.setLevel(self.__config_manager.config["logging"]["file_log_level"])
            active_handlers.append(file_handler)

        logging.basicConfig(format=self.__config_manager.config["logging"]["log_format"], level=logging.DEBUG, handlers=active_handlers)

        logging.getLogger("PIL").setLevel(logging.WARNING)
        logging.getLogger("urllib").setLevel(logging.WARNING)
        self.__logger = logging.getLogger(__name__)

    def __init__(self):
        self.__running = False
        self.__logger = None

        self.__config_manager = managers.ConfigManager(self)
        self.__config_manager.load_cfg()

        self.__setup_logging()

        self.__logger.log(logging.INFO, "Bot init")

        print(r" _______     _____ _____   _____ ____        _   ")
        print(r"|__   __|   |_   _|  __ \ / ____|  _ \      | |  ")
        print(r"   | |_      _| | | |__) | |    | |_) | ___ | |_ ")
        print(r"   | \ \ /\ / / | |  _  /| |    |  _ < / _ \| __|")
        print(r"   | |\ V  V /| |_| | \ \| |____| |_) | (_) | |_ ")
        print(r"   |_| \_/\_/_____|_|  \_\\_____|____/ \___/ \__|")

        self.__data_manager = managers.DataManager(self)
        self.__data_manager.setup_database()
        self.__distribution_manager = managers.MessageDistributor(self)
        self.__connection = connection.IRCConnection(self)
        self.__cron_manager = managers.CronManager(self)
        self.__cron_manager.load_cron_jobs()
        self.__plugin_manager = managers.PluginManager(self)
        self.__plugin_manager.load_plugins()
        self.__currency_manager = managers.CurrencyManager(self)
        self.__currency_manager.load_settings()
        self.__heartbeat_manager = managers.HeartbeatManager(self)
        self.__heartbeat_manager.load_settings()
        self.__heartbeat_manager.add_observer(self.__currency_manager)

    def start(self):
        self.__logger.log(logging.INFO, "Bot started")
        # ansi color support for cmd
        self.enable_cmd_colors()

        self.__distribution_manager.start()
        self.__connection.connect()
        self.__heartbeat_manager.start()
        self.__cron_manager.start()
        self.__running = True

        while self.__running:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                self.__close()
        self.__close()

    # def refresh(self):
    #     #self.__config_manager
    #
    #     self.__connection.refresh()
    #     self.__data_manager.refresh()
    #     self.__cron_manager.refresh()
    #     self.__heartbeat_manager.refresh()
    #     self.__currency_manager.refresh()
    #     self.__plugin_manager.refresh()
    #     self.__distribution_manager.refresh()

    def stop(self):
        self.__running = False

    def __close(self):
        print("Bot closing")
        self.__logger.log(logging.DEBUG, "Bot shutting down")
        self.__running = False
        self.__currency_manager.close()
        self.__heartbeat_manager.close()
        self.__cron_manager.close()
        self.__distribution_manager.close()
        self.__plugin_manager.close()
        self.__connection.close()
        self.__data_manager.close()

    def get_data_manager(self):
        return self.__data_manager

    def get_distribution_manager(self):
        return self.__distribution_manager

    def get_plugin_manager(self):
        return self.__plugin_manager

    def get_connection(self):
        return self.__connection

    def get_config_manager(self):
        return self.__config_manager

    def get_currency_manager(self):
        return self.__currency_manager

    def get_heartbeat_manager(self):
        return self.__heartbeat_manager


if __name__ == '__main__':
    bot = Bot()
    bot.start()

