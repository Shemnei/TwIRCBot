import logging
import time

logger = logging.getLogger(__name__)


class Plugin:

    def __init__(self):
        self.bot = None
        self.connection = None
        self.plugin_manager = None
        self.config = None
        self.data_manager = None

    def get_regex(self):
        """
        Called for every received line, if matches cmd() of plugin will be called
        :return: a regex string
        """
        return r"."

    def cmd(self, message):
        """
        Will be called if get_regex() matched line.
        :param message: namedtuple Message(user, tags, cm)
        """
        pass

    def on_load(self, bot):
        """Called once when the bot first loads the plugin"""
        self.bot = bot
        self.connection = bot.get_connection()
        self.plugin_manager = bot.get_plugin_manager()
        self.config = bot.get_config_manager()
        self.data_manager = bot.get_data_manager()

    def on_refresh(self):
        """Called every time the bot refreshes/reloads its plugins"""
        pass

    def on_close(self):
        """Gets called when bot/connection is closed"""
        logging.log(logging.INFO, "Closing [%s]" % self.__module__)

    def on_channel_change(self, new_channel):
        """
        Called whenever the bot switches channel.
        :param new_channel: new connected channel
        """
        pass


class FilterPlugin(Plugin):

    FILTER = "ni"
    DESCRIPTION = "ni"
    PERMISSION_LEVEL = 0        # <- if your level higher then filter wont affect message

    def __init__(self):
        super().__init__()

    def on_load(self, bot):
        super().on_load(bot)
        self.plugin_manager.register_filter(self.FILTER, self.DESCRIPTION, self.PERMISSION_LEVEL)
        logging.log(logging.INFO, "+Filter %s loaded" % self.__module__)


class CommandPlugin(Plugin):

    COMMAND = "ni"
    ARGS = ""
    DESCRIPTION = "ni"
    PERMISSION_LEVEL = 0        # <- your level needs to same or higher to execute command
    ADD_TO_HELP = False

    # TODO Implement
    CURRENCY_COST = 0
    COOL_DOWN = 0
    IS_COOL_DOWN_GLOBAL = False

    def __init__(self):
        super().__init__()
        self.__user_calls = {}
        self.__last_global_call = None

    def is_valid_request(self, user):
        if self.IS_COOL_DOWN_GLOBAL:

            valid = False
            if user.name == self.config.config["connection"]["nick_name"].lower() \
                    or user.name == self.config.config["connection"]["channel"].lower() \
                    or not self.__last_global_call \
                    or ((time.time() - self.__last_global_call >= self.COOL_DOWN
                         and user.perm_lvl >= self.PERMISSION_LEVEL)):
                valid = True
                self.__last_global_call = time.time()
            return valid

        else:
            user_last_call = self.__user_calls.get(user.name, 0)
            if user.name == self.config.config["connection"]["nick_name"].lower() \
                    or user.name == self.config.config["connection"]["channel"].lower() \
                    or (time.time() - user_last_call >= self.COOL_DOWN and user.perm_lvl >= self.PERMISSION_LEVEL):
                self.__user_calls[user.name] = time.time()
                return True
            return False

    def on_load(self, bot):
        super().on_load(bot)
        self.plugin_manager.register_command(self.COMMAND, self.ARGS, self.DESCRIPTION, self.PERMISSION_LEVEL,
                                             self.ADD_TO_HELP)
        logging.log(logging.INFO, "+Command %s loaded" % self.__module__)

    def get_usage(self):
        return self.COMMAND + " " + self.ARGS + " - " + self.DESCRIPTION


class GenericPlugin(Plugin):

    def __init__(self):
        super().__init__()

    def on_load(self, bot):
        super().on_load(bot)
        logging.log(logging.INFO, "+Plugin %s loaded" % self.__module__)


class Observable:
    """
    Simple implementation of the observer pattern
    """

    def __init__(self):
        self.__registered_observers = []

    def add_observer(self, observer):
        if observer not in self.__registered_observers:
            self.__registered_observers.append(observer)

    def remove_observer(self, observer):
        if observer in self.__registered_observers:
            self.__registered_observers.remove(observer)

    def notify_observers(self, arg=None):
        local_list = self.__registered_observers[:]
        for observer in local_list:
            observer.update(self, arg)

    def remove_observers(self):
        self.__registered_observers = []


class Observer:
    """
    Simple implementation of the observer pattern
    """

    def update(self, observable, args):
        pass
