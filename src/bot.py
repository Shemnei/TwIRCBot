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

        self.__cfg = config
        self.__connection = connection.IRCConnection(self)
        self.__cron_task = cron.CronTask(self)
        self.__cron_task.load_cron_jobs()
        self.__plugin_manager = managers.PluginManager(self)
        self.__plugin_manager.load_plugins()

    def start(self):
        # ansi color support for cmd
        enable_cmd_colors()

        self.__connection.connect()
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
        self.__cron_task.close()
        self.__plugin_manager.close()
        self.__connection.close()

    def get_plugin_manager(self):
        return self.__plugin_manager

    def get_connection(self):
        return self.__connection

    def get_config_manager(self):
        return self.__cfg

if __name__ == '__main__':
    bot = Bot(cfg.config)
    bot.start()

