import ctypes
import datetime
import logging
from logging import handlers
import platform
import time

import cfg
import connection
import managers


# setting up logging
FORMAT = '[%(asctime)s / %(name)s / %(levelname)s] %(message)s'

file_handler = logging.handlers.RotatingFileHandler(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + "_botlog.txt")
file_handler.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

logging.basicConfig(format=FORMAT, level=logging.DEBUG, handlers=[file_handler, console_handler])

pil_logger = logging.getLogger("PIL").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
#


def enable_cmd_colors():
    # Windows 10 build 10586: Added support to ANSI colors, enabled by default
    # Windows 10 build 14393: ANSI colors are still supported, but not default
    plt = platform.platform().split(".")
    if plt[0] == "Windows-10" and int(plt[2]) >= 14393:
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        logger.log(logging.DEBUG, "Ansi escape sequence enabled [%s]" % platform.platform())


class Bot:

    def __init__(self, config):
        self.__running = False

        logger.log(logging.INFO, "Bot init")

        print(r" _______     _____ _____   _____ ____        _   ")
        print(r"|__   __|   |_   _|  __ \ / ____|  _ \      | |  ")
        print(r"   | |_      _| | | |__) | |    | |_) | ___ | |_ ")
        print(r"   | \ \ /\ / / | |  _  /| |    |  _ < / _ \| __|")
        print(r"   | |\ V  V /| |_| | \ \| |____| |_) | (_) | |_ ")
        print(r"   |_| \_/\_/_____|_|  \_\\_____|____/ \___/ \__|")

        self.__cfg = config
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
        logger.log(logging.INFO, "Bot started")
        # ansi color support for cmd
        enable_cmd_colors()

        self.__distribution_manager.start()
        self.__connection.connect()
        self.__heartbeat_manager.start()
        self.__cron_manager.start()
        self.__running = True

        while self.__running:
            try:
                time.sleep(5)
            except KeyboardInterrupt:
                self.__close()
        self.__close()

    def stop(self):
        self.__running = False

    def __close(self):
        logger.log(logging.DEBUG, "Bot shutting down")
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
        return self.__cfg

    def get_currency_manager(self):
        return self.__currency_manager

    def get_heartbeat_manager(self):
        return self.__heartbeat_manager


if __name__ == '__main__':
    bot = Bot(cfg.config)
    bot.start()

