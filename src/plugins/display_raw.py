import master


class IRCPlugin(master.Plugin):

    _active = False

    def get_regex(self):
        if IRCPlugin._active:
            return r"."
        else:
            return r"$ä"

    def cmd(self, line):
        print(line)
