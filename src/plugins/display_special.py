import datetime

import master


class IRCPlugin(master.Plugin):

    def get_regex(self):
        return r"."

    # TODO: maybe support for notice
    def cmd(self, line):
        tag_cmp = None
        parts = line.split()
        offset = 0
        disp_name = None
        if line.startswith('@'):
            offset = 1
            tag_cmp = self.connection.parse_tags(parts[0])
            disp_name = tag_cmp.get("display-name", None)

        sender = parts[0 + offset]
        command = parts[1 + offset]

        if command == "PRIVMSG":
            return
        elif command == "ROOMSTATE":
            if tag_cmp:
                if tag_cmp.get("slow", None):
                    print_tm("SERVER: Channel is slow mode [%ss]" % tag_cmp["slow"])
                if tag_cmp.get("r9k", None):
                    if tag_cmp["r9k"] == '1':
                        print_tm("SERVER: Channel has r9k active")
                    else:
                        print_tm("SERVER: Channel has no r9k")
                if tag_cmp.get("subsonly", None):
                    if tag_cmp["subsonly"] == '1':
                        print_tm("SERVER: Channel is in sub only mode")
                    else:
                        print_tm("SERVER: Channel is no longer in sub only mode")
                return
        elif command == "421":
            print_tm("SERVER: Unknown command %s" % parts[3 + offset])
            return
        elif command == "JOIN":
            print_tm("SERVER: %s joined the channel" % (disp_name or sender[1 + offset:sender.find('!')]))
            return
        elif command == "PART":
            print_tm("SERVER: %s left the channel" % (disp_name or sender[1 + offset:sender.find('!')]))
            return
        elif command == "MODE":
            if parts[3 + offset] == "+o":
                print_tm("SERVER: %s was promoted to operator" % (disp_name or parts[4 + offset]))
                return
            elif parts[3 + offset] == "-o":
                print_tm("SERVER: %s lost operator rank" % (disp_name or parts[4 + offset]))
                return
            return
        elif command == "NOTICE":
            parts[3 + offset] = parts[3 + offset].lstrip(':')
            print_tm("SERVER: " + " ".join(parts[3 + offset:]))
            return
        elif command == "USERNOTICE":
            if tag_cmp:
                if tag_cmp.get("systemmsg", None):
                    print_tm("SERVER: " + tag_cmp["systemmsg"])
                    return
            print_tm("SERVER: SUB/RESUB")
            return
        elif command == "HOSTTARGET":
            if parts[3].lstrip(':') == "-":
                print_tm("SERVER: %s stopped hosting" % (disp_name or (parts[2 + offset].lstrip('#'))))
                return
            else:
                print_tm("SERVER: Hosted by %s for %s viewers" % (disp_name or parts[2 + offset].lstrip('#'),
                                                                  parts[4 + offset].strip("[]")))
                return
        elif command == "CLEARCHAT":
            if parts[-1].startswith(':'):
                if tag_cmp:
                    if tag_cmp.get("banduration", None):
                        print_tm("SERVER: %s timed out [%ss/%s]" % (disp_name or parts[3 + offset].lstrip(":"),
                                                                    tag_cmp["banduration"],
                                                                    tag_cmp.get("banreason", "").replace("\s", " ")))
                        return
                    else:
                        print_tm("SERVER: %s banned [%s]" % (disp_name or parts[3 + offset].lstrip(":"),
                                                             tag_cmp.get("banreason", "").replace("\s", " ")))
                        return
                else:
                    print_tm("SERVER: %s timeout or banned" % (disp_name or parts[3 + offset].lstrip(":")))
            else:
                print_tm("SERVER: Channel cleared")
                return
        elif command == "001":
            print_tm("CONNECTED TO IRC SERVER")
            return
        elif command == "CAP":
            parts[4 + offset] = parts[4].lstrip(':')
            if parts[3 + offset] == "ACK":
                print_tm("SERVER: Acknowledged %s" % (" ".join(parts[4 + offset:])))
                return
            else:
                print_tm("SERVER: Ignored %s" % (" ".join(parts[4 + offset:])))
                return
        elif command == "RECONNECT":
            print_tm("SERVER RESTART SHORTLY")
            return


def print_tm(msg):
    # FIXME: Colors are tmp
    print("[" + datetime.datetime.now().strftime("%H:%M:%S") + "] \033[37m" + msg + "\033[0m")
