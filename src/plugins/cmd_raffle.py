import random
import re
import threading
import time

import master


class IRCPlugin(master.CommandPlugin):

    def __init__(self):
        super().__init__()
        self.__running = False
        self.__entries = []
        self.__random = random.seed()
        self.__id = 0

    # raffle (start, close, join, draw_other) (automate_close_time)
    def get_regex(self):
        return r"(@.* )?:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :!raffle "

    def cmd(self, message):
        args = message.msg.replace("!raffle ", '').split()

        if message.user[1] >= self.data_manager.PermissionLevel.moderator:

            if args[0] == "start":

                if self.__running:
                    self.connection.add_chat_msg("There is currently another raffle running!")
                else:
                    self.__id += 1
                    self.__running = True
                    self.__entries = []
                    self.connection.add_chat_msg("Raffle started! Join with !raffle join.")
                    if len(args) == 2 and args[1].isnumeric():
                        counter = int(args[1])
                        self.connection.add_chat_msg("Raffle self closing in %is" % counter)
                        c = threading.Thread(target=self.self_closing, args=(self.__id, counter), name="self_closing_raffle_thread")
                        c.start()

            elif args[0] == "close":

                if self.__running:
                    self.__running = False
                    # remove identical records
                    self.__entries = list(set(self.__entries))
                    if len(self.__entries) == 0:
                        self.connection.add_chat_msg("Raffle ended! No entries :(")
                    else:
                        self.connection.add_chat_msg("Raffle ended! Drawing winner!")
                        random.shuffle(self.__entries)
                        winner = random.choice(self.__entries)
                        self.__entries.remove(winner)
                        self.connection.add_chat_msg("The winner is %s. Congratulation!" % winner)
                        self.connection.add_chat_msg(".w %s The winner of raffle %i is %s." % (self.config["connection"]["channel"], self.__id , winner))
                else:
                    self.connection.add_chat_msg("There is currently no raffle running!")

            elif args[0] == "draw_other":

                if len(self.__entries) > 0:
                    self.connection.add_chat_msg("Drawing another winner!")
                    random.shuffle(self.__entries)
                    winner = random.choice(self.__entries)
                    self.__entries.remove(winner)
                    self.connection.add_chat_msg("The winner is %s. Congratulation!" % winner)
                    self.connection.add_chat_msg(".w %s The winner of raffle %i is %s." % (
                        self.config["connection"]["channel"], self.__id, winner))
                else:
                    self.connection.add_chat_msg("There are no entries!")

        elif args[0] == "join":

            if self.__running:
                self.connection.add_chat_msg(".w %s You entered the raffle!" % message.user[0])
                self.__entries.append(message.user[0])
            else:
                self.connection.add_chat_msg("There is currently no raffle running!")



    def self_closing(self, raffle_id, countdown):
        time.sleep(countdown)
        if raffle_id == self.__id:
            self.connection.add_received_msg("!raffle close")

    def get_description(self):
        return "!raffle (start/close/join) (time_to_auto_close) - Opens a raffle to draw a random winner"
