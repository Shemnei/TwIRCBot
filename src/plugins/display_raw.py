import master


class IRCPlugin(master.GenericPlugin):

    def get_regex(self):
        return r"."

    def cmd(self, message):
        print(message.raw_line)
