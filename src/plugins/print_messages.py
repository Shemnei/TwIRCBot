import datetime

import master


class IRCPlugin(master.GenericPlugin):

    def get_regex(self):
        return r"(PRIVMSG|WHISPER) #?\w+ :"

    def cmd(self, message):
        user = message.user.name
        title = ""
        color = None
        if message.tags:
            tmp = ""
            if message.tags.get("turbo", None) == "1":
                tmp += "T/"
            if message.tags.get("subscriber", None) == "1":
                tmp += "S/"
                color = self.bot.Color.BRIGHT_YELLOW
            if message.tags.get("mod", None) == "1":
                tmp += "M/"
                color = self.bot.Color.BRIGHT_RED
            if message.tags.get("bits", None):
                tmp += "C" + message.tags["bits"] + "/"
                color = self.bot.Color.BRIGHT_BLUE
            if "broadcaster/1" in message.tags.get("badges", ""):
                tmp += "B"
                color = self.bot.Color.BRIGHT_MAGENTA
            tmp = tmp.rstrip("/")
            title = "| (%s) " % tmp
            if message.tags.get("display-name", None):
                user = message.tags["display-name"]

        if message.cmd == "WHISPER":
            self.print_tm(user + " -> " + message.channel + ": " + message.msg, self.bot.Color.BRIGHT_CYAN)
        else:
            if user == "twitchnotify":
                self.print_tm("NOTIFY: " + message.msg, self.bot.Color.BRIGHT_BLUE)
            else:
                self.print_tm(title + user + ": " + message.msg, color)

    def print_tm(self, msg, color=None):
        if color is None:
            print("[" + datetime.datetime.now().strftime("%H:%M:%S") + "] " + msg)
        else:
            print("[" + datetime.datetime.now().strftime("%H:%M:%S") + "] " + color + msg + self.bot.Color.RESET)

