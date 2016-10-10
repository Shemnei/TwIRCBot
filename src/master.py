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
        print("Closing [%s]" % self.__module__)

    def get_description(self):
        """
        For now only needed for commands (cmd_name.py), used for the help command.
        syntax: !command_name args - description
        :return: info about command usage
        """
        return "not implemented"

    def on_channel_change(self, new_channel):
        """
        Called whenever the bot switches channel.
        :param new_channel: new connected channel
        """
        pass


class FilterPlugin(Plugin):

    DESCRIPTION = "ni"
    PERMISSION_LEVEL = 0        # <- if your level higher then filter wont affect message

    def __init__(self):
        super().__init__()

    def on_load(self, bot):
        super().on_load(bot)
        print("+Filter %s loaded" % self.__module__)


class CommandPlugin(Plugin):

    COMMAND = "ni"
    DESCRIPTION = "ni"
    ADD_TO_HELP = False
    PERMISSION_LEVEL = 0        # <- your level needs to same or higher to execute command
    COOL_DOWN = 0

    def __init__(self):
        super().__init__()

    def on_load(self, bot):
        super().on_load(bot)
        print("+Command %s loaded" % self.__module__)

    def get_usage(self):
        return "not implemented"


class GenericPlugin(Plugin):

    def __init__(self):
        super().__init__()

    def on_load(self, bot):
        super().on_load(bot)
        print("+Plugin %s loaded" % self.__module__)


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
