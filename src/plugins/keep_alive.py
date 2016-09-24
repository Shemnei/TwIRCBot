import master


class IRCPlugin(master.Plugin):

    def get_regex(self):
        return r"^PING :"

    def cmd(self, line):
        pong_msg = line.replace("PING", "PONG")
        self.connection.add_raw_msg(pong_msg, important=True)
        print("PING > %s" % pong_msg)
