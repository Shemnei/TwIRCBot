import datetime

import master


class IRCPlugin(master.GenericPlugin):

    def get_regex(self):
        return r"$"

    # TODO: maybe support for notice
    # TODO REWORK WITH NEW MESSAGE
    def cmd(self, message):
        line = message.raw_line
        tag_cmp = message.tags
        parts = line.split()
        offset = 0
        display_name = None
        if tag_cmp:
            offset = 1
            display_name = tag_cmp.get("display-name", None)

        sender = parts[0 + offset]
        command = parts[1 + offset]

        if command == "PRIVMSG":
            return
        elif command == "ROOMSTATE":
            if tag_cmp:
                if tag_cmp.get("slow", None):
                    self.print_tm("SERVER: Channel is slow mode [%ss]" % tag_cmp["slow"])
                if tag_cmp.get("r9k", None):
                    if tag_cmp["r9k"] == '1':
                        self.print_tm("SERVER: Channel has r9k active")
                    else:
                        self.print_tm("SERVER: Channel has no r9k")
                if tag_cmp.get("subsonly", None):
                    if tag_cmp["subsonly"] == '1':
                        self.print_tm("SERVER: Channel is in sub only mode")
                    else:
                        self.print_tm("SERVER: Channel is no longer in sub only mode")
                return
        elif command == "421":
            self.print_tm("SERVER: Unknown command %s" % parts[3 + offset])
            return
        elif command == "JOIN":
            self.print_tm("SERVER: %s joined the channel" % (display_name or sender[1 + offset:sender.find('!')]))
            return
        elif command == "PART":
            self.print_tm("SERVER: %s left the channel" % (display_name or sender[1 + offset:sender.find('!')]))
            return
        elif command == "MODE":
            if parts[3 + offset] == "+o":
                self.print_tm("SERVER: %s was promoted to operator" % (display_name or parts[4 + offset]))
                return
            elif parts[3 + offset] == "-o":
                self.print_tm("SERVER: %s lost operator rank" % (display_name or parts[4 + offset]))
                return
            return
        elif command == "NOTICE":
            parts[3 + offset] = parts[3 + offset].lstrip(':')
            self.print_tm("SERVER: " + " ".join(parts[3 + offset:]))
            return
        elif command == "USERNOTICE":
            if tag_cmp:
                if tag_cmp.get("system-msg", None):
                    self.print_tm("SERVER: " + tag_cmp["system-msg"].replace("\s", " "))
                    return
            self.print_tm("SERVER: SUB/RESUB")
            return
        elif command == "HOSTTARGET":
            if parts[3 + offset].startswith("-"):
                self.print_tm("SERVER: %s stopped hosting" % (display_name or (parts[2 + offset].lstrip('#'))))
                return
            else:
                self.print_tm("SERVER: %s hosting %s for %s viewers" %
                         (parts[2 + offset][1:], parts[3 + offset][1:], parts[4 + offset].strip("[]")))
                return
        elif command == "CLEARCHAT":
            if parts[-1].startswith(':'):
                if tag_cmp:
                    if tag_cmp.get("banduration", None):
                        self.print_tm("SERVER: %s timed out [%ss/%s]" % (display_name or parts[3 + offset].lstrip(":"),
                                                                    tag_cmp["banduration"],
                                                                    tag_cmp.get("banreason", "").replace("\s", " ")))
                        return
                    else:
                        self.print_tm("SERVER: %s banned [%s]" % (display_name or parts[3 + offset].lstrip(":"),
                                                             tag_cmp.get("banreason", "").replace("\s", " ")))
                        return
                else:
                    self.print_tm("SERVER: %s timeout or banned" % (display_name or parts[3 + offset].lstrip(":")))
            else:
                self.print_tm("SERVER: Channel cleared")
                return
        elif command == "001":
            self.print_tm("CONNECTED TO IRC SERVER")
            return
        elif command == "CAP":
            parts[4 + offset] = parts[4].lstrip(':')
            if parts[3 + offset] == "ACK":
                self.print_tm("SERVER: Acknowledged %s" % (" ".join(parts[4 + offset:])))
                return
            else:
                self.print_tm("SERVER: Ignored %s" % (" ".join(parts[4 + offset:])))
                return
        elif command == "RECONNECT":
            self.print_tm("SERVER RESTART SHORTLY")
            return

    def print_tm(self, msg):
        print("[" + datetime.datetime.now().strftime("%H:%M:%S") + "] " + self.connection.Color.BRIGHT_WHITE + msg
              + self.connection.Color.RESET)
