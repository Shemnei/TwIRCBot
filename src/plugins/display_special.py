import datetime

import re

import master


class IRCPlugin(master.Plugin):

    _active = True

    def get_regex(self):
        if IRCPlugin._active:
            return r"."
        else:
            return r"$ä"

    def cmd(self, line):
        parts = line.split()
        sender = parts[0]
        command = parts[1]

        if command == "PRIVMSG":
            return
        elif command == "421":
            print("[" + datetime.datetime.now().strftime("%H:%M:%S") + "] SERVER: Unknown command %s" % parts[3])
            return
        elif command == "JOIN":
            print("[" + datetime.datetime.now().strftime("%H:%M:%S") + "] SERVER: %s joined the channel" % sender[1:sender.find('!')])
            return
        elif command == "PART":
            print("[" + datetime.datetime.now().strftime("%H:%M:%S") + "] SERVER: %s left the channel" % sender[1:sender.find('!')])
            return
        elif command == "MODE":
            if parts[3] == "+o":
                print("[" + datetime.datetime.now().strftime("%H:%M:%S") + "] SERVER: %s was promoted to operator" % parts[4])
                return
            elif parts[3] == "-o":
                print("[" + datetime.datetime.now().strftime("%H:%M:%S") + "] SERVER: %s lost operator rank" % parts[4])
                return
            return
        elif command == "NOTICE":
            parts[3] = parts[3].lstrip(':')
            print("[" + datetime.datetime.now().strftime("%H:%M:%S") + "] SERVER: " + " ".join(parts[3:]))
            return
        elif command == "USERNOTICE":
            print("[" + datetime.datetime.now().strftime("%H:%M:%S") + "] SERVER: SUB/RESUB")
            return
        elif command == "HOSTTARGET":
            if parts[3].lstrip(':') == "-":
                print("[" + datetime.datetime.now().strftime("%H:%M:%S") + "] SERVER: %s stopped hosting" % (parts[2].lstrip('#')))
                return
            else:
                print("[" + datetime.datetime.now().strftime("%H:%M:%S") + "] SERVER: Hosted by %s for %s viewers" % (parts[2].lstrip('#'), parts[4].strip("[]")))
                return
        elif command == "CLEARCHAT":
            if parts[-1].startswith(':'):
                print("[" + datetime.datetime.now().strftime("%H:%M:%S") + "] SERVER: %s banned or timout" % parts[3].lstrip(":"))
                return
            else:
                print("[" + datetime.datetime.now().strftime("%H:%M:%S") + "] SERVER: Channel cleared")
                return
        elif command == "001":
            print("[" + datetime.datetime.now().strftime("%H:%M:%S") + "] CONNECTED TO IRC SERVER")
            return
        elif command == "CAP":
            parts[4] = parts[4].lstrip(':')
            if parts[3] == "ACK":
                print("[" + datetime.datetime.now().strftime("%H:%M:%S") + "] SERVER: Acknowledged %s" % (" ".join(parts[4:])))
                return
            else:
                print("[" + datetime.datetime.now().strftime("%H:%M:%S") + "] SERVER: Ignored %s" % (" ".join(parts[4:])))
                return
        elif command == "RECONNECT":
            print("[" + datetime.datetime.now().strftime("%H:%M:%S") + "] SERVER RESTART SHORTLY")
            return
