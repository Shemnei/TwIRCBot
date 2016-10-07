import datetime
import re

import master


class IRCPlugin(master.GenericPlugin):

    def get_regex(self):
        return r"(@.* )?:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :"

    def cmd(self, message):
        user = message.user[0]
        title = ""
        color = None
        if message.tags:
            tmp = ""
            if message.tags.get("turbo", None) == "1":
                tmp += "T/"
            if message.tags.get("subscriber", None) == "1":
                tmp += "S/"
                color = self.connection.Color.BRIGHT_YELLOW
            if message.tags.get("mod", None) == "1":
                tmp += "M/"
                color = self.connection.Color.BRIGHT_RED
            if message.tags.get("bits", None):
                tmp += message.tags["bits"] + "/"
                color = self.connection.Color.BRIGHT_BLUE
            if "broadcaster/1" in message.tags.get("badges", ""):
                tmp += "B"
                color = self.connection.Color.BRIGHT_MAGENTA
            tmp = tmp.strip("/")
            title = "| (%s) " % tmp
            if message.tags.get("display-name", None):
                user = message.tags["display-name"]

        if user == "twitchnotify":
            print_tm("NOTIFY: " + message.msg, self.connection.Color.BRIGHT_BLUE)
        else:
            print_tm(title + user + ": " + message.msg, color)


def print_tm(msg, color=None):
    if color is None:
        print("[" + datetime.datetime.now().strftime("%H:%M:%S") + "] " + msg)
    else:
        print("[" + datetime.datetime.now().strftime("%H:%M:%S") + "] " + color + msg + "\033[0m")

