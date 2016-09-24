import inspect


class Plugin:

    def __init__(self):
        self.connection = None

    def get_regex(self):
        """
        Called for every received line, if matches cmd() of plugin will be called
        :return: a regex string
        """
        return r"."

    def cmd(self, line):
        """
        Will be called if get_regex() matched line.
        :param line: received line (without trailing \r\n)
        """
        pass

    def on_load(self, connection):
        """Called once when the bot first loads the plugin"""
        self.connection = connection
        print("Plugin %s loaded" % self.__module__)

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
