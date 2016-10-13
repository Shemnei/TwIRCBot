import logging
import random
import threading
import time

import master

logger = logging.getLogger(__name__)


class IRCPlugin(master.CommandPlugin):

    COMMAND = "!raffle"
    ARGS = "[start/close/join] (time_to_auto_close)"
    DESCRIPTION = "Opens a raffle to draw a random winner"
    PERMISSION_LEVEL = 0
    ADD_TO_HELP = True

    def __init__(self):
        super().__init__()
        self.__running = False
        self.__entries = []
        self.__random = random.seed()
        self.__id = 0

    def get_regex(self):
        return r"PRIVMSG #\w+ :!raffle \w+"

    def cmd(self, message):
        args = message.msg[8:].split()

        if message.user[1] >= self.data_manager.PermissionLevel.moderator \
                or message.user[0] == self.config["connection"]["nick_name"].lower() \
                or message.user[0] == self.config["connection"]["channel"]:

            if args[0] == "start":

                if self.__running:
                    logger.log(logging.DEBUG, "@%s -> raffle start - raffle running" % message.user[0])
                    self.connection.add_chat_msg("There is currently another raffle running!")
                else:
                    self.__id += 1
                    self.__running = True
                    self.__entries = []
                    self.connection.add_chat_msg("Raffle started! Join with !raffle join.")
                    if len(args) == 2 and args[1].isnumeric():
                        counter = int(args[1])
                        logger.log(logging.DEBUG, "@%s -> raffle start self_closing:%i" % (message.user[0], counter))
                        self.connection.add_chat_msg("Raffle self closing in %is" % counter)
                        threading.Thread(target=self.__self_closing_routine, args=(self.__id, counter),
                                         name="self_closing_raffle_thread").start()
                    else:
                        logger.log(logging.DEBUG, "@%s -> raffle start" % message.user[0])

            elif args[0] == "close":

                if self.__running:
                    logger.log(logging.DEBUG, "@%s -> raffle close" % message.user[0])
                    self.__running = False
                    # removes identical records
                    self.__entries = list(set(self.__entries))
                    if len(self.__entries) == 0:
                        self.connection.add_chat_msg("Raffle ended! No entries :(")
                    else:
                        self.connection.add_chat_msg("Raffle ended! Drawing winner!")
                        self.__draw_and_handle_winner()
                else:
                    logger.log(logging.DEBUG, "@%s -> raffle close - no raffle running" % message.user[0])
                    self.connection.add_chat_msg("There is currently no raffle running!")

            elif args[0] == "draw_other":

                if len(self.__entries) > 0 and not self.__running:
                    logger.log(logging.DEBUG, "@%s -> raffle draw_other" % message.user[0])
                    self.connection.add_chat_msg("Drawing another winner!")
                    self.__draw_and_handle_winner()
                else:
                    logger.log(logging.DEBUG, "@%s -> raffle draw_other - invalid" % message.user[0])
                    self.connection.add_chat_msg("There are no entries or another raffle is already running!")

        if args[0] == "join":

            if self.__running:
                logger.log(logging.DEBUG, "@%s -> raffle join" % message.user[0])
                self.connection.add_chat_msg(".w %s You entered the raffle!" % message.user[0])
                self.__entries.append(message.user[0])
            else:
                logger.log(logging.DEBUG, "@%s -> raffle join - no raffle running" % message.user[0])
                self.connection.add_chat_msg("There is currently no raffle running!")

    def __draw_and_handle_winner(self):
        winner = random.choice(self.__entries)
        self.__entries.remove(winner)
        logger.log(logging.DEBUG, "@raffle -> raffle %i winner: %s" % (self.__id, winner))
        self.connection.add_chat_msg("The winner is %s. Congratulation!" % winner)
        self.connection.add_chat_msg(".w %s The winner of raffle #%i is %s." % (
            self.config["connection"]["channel"], self.__id, winner))

    def __self_closing_routine(self, raffle_id, countdown):
        time.sleep(countdown)
        if raffle_id == self.__id:
            logger.log(logging.DEBUG, "@raffle -> raffle %i timer_triggered[%is]" % (self.__id, countdown))
            self.connection.add_received_msg("!raffle close")
