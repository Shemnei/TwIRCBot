import master


class IRCPlugin(master.Plugin):

    def get_regex(self):
        return r"."

    def cmd(self, line):
        print(line)
