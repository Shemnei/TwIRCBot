import ctypes
import platform
import time

import cfg
import connection
import cron
import managers


def enable_cmd_colors():
    # Windows 10 build 10586: Added support to ANSI colors, enabled by default
    # Windows 10 build 14393: ANSI colors are still supported, but not default
    plt = platform.platform().split(".")
    if plt[0] == "Windows-10" and int(plt[2]) >= 14393:
        print("DEBUG: Ansi escape sequence enabled [%s]" % platform.platform())
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)


class Bot:

    def __init__(self, config):
        self.__running = False

        print(r" _______     _____ _____   _____ ____        _   ")
        print(r"|__   __|   |_   _|  __ \ / ____|  _ \      | |  ")
        print(r"   | |_      _| | | |__) | |    | |_) | ___ | |_ ")
        print(r"   | \ \ /\ / / | |  _  /| |    |  _ < / _ \| __|")
        print(r"   | |\ V  V /| |_| | \ \| |____| |_) | (_) | |_ ")
        print(r"   |_| \_/\_/_____|_|  \_\\_____|____/ \___/ \__|")

        self.__cfg = config
        self.__data_manager = managers.DataManager(self)
        self.__data_manager.setup_database()
        self.__connection = connection.IRCConnection(self)
        self.__cron_task = cron.CronTask(self)
        self.__cron_task.load_cron_jobs()
        self.__plugin_manager = managers.PluginManager(self)
        self.__plugin_manager.load_plugins()
        self.__currency_manager = managers.CurrencyManager(self)
        self.__currency_manager.load_settings()

    def start(self):
        # ansi color support for cmd
        enable_cmd_colors()

        self.__connection.connect()
        self.__currency_manager.start()
        self.__cron_task.start()
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
        print("DEBUG: Bot shutting down")
        self.__running = False
        self.__currency_manager.close()
        self.__cron_task.close()
        self.__plugin_manager.close()
        self.__connection.close()

    def get_data_manager(self):
        return self.__data_manager

    def get_plugin_manager(self):
        return self.__plugin_manager

    def get_connection(self):
        return self.__connection

    def get_config_manager(self):
        return self.__cfg

    def get_currency_manager(self):
        return self.__currency_manager

if __name__ == '__main__':
    bot = Bot(cfg.config)
    bot.start()

