import logging
import queue
import socket
import ssl
import threading
import time

logger = logging.getLogger(__name__)


class IRCConnection:

    def __init__(self, bot):
        self.__bot = bot
        self.__config = bot.get_config_manager()
        self.__distribution_manager = bot.get_distribution_manager()

        self.__running = False
        self.__active_channel = None
        self.__send_thread = threading.Thread(target=self.__send_routine, name="send_thread")
        self.__receive_thread = threading.Thread(target=self.__receive_routine, name="receive_thread")

        self.__plugin_manager = None
        self.__irc_socket = None
        self.__send_queue = queue.Queue()

    def connect(self, reconnect=False):
        self.__running = True
        self.__plugin_manager = self.__bot.get_plugin_manager()
        start_connect = time.time()

        tmp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        if self.__config.config["connection"]["ssl"]:
            self.__irc_socket = ssl.wrap_socket(tmp)
        else:
            self.__irc_socket = tmp

        self.__irc_socket.connect((self.__config.config["connection"]["server"], self.__config.config["connection"]["port"]))
        logger.log(logging.INFO, "Connected to %s on %i" % (self.__config.config["connection"]["server"],
                                                             self.__config.config["connection"]["port"]))
        if not self.__send_thread.is_alive():
            self.__send_thread.start()
            logger.log(logging.DEBUG, "Send Thread started")
        if not self.__receive_thread.is_alive():
            self.__receive_thread.start()
            logger.log(logging.DEBUG, "Receive Thread started")

        req_str = ""
        if self.__config.config["connection"]["membership_messages"]:
            req_str += "twitch.tv/membership "
        if self.__config.config["connection"]["tags"]:
            req_str += "twitch.tv/tags "
        if self.__config.config["connection"]["commands"]:
            req_str += "twitch.tv/commands"

        oauth = self.__config.config["connection"]["oauth_token"]
        if not oauth.startswith("oauth:"):
            oauth = "oauth:" + oauth

        self.__send_queue.put("CAP REQ :%s" % req_str.rstrip())
        self.__send_queue.put('PASS %s' % oauth)
        self.__send_queue.put('NICK %s' % self.__config.config["connection"]["nick_name"].lower())

        self.join_channel(self.__config.config["connection"]["channel"], reconnect=reconnect)

        logger.log(logging.DEBUG, "Connection established in %fms" % ((time.time() - start_connect)*1000))

    def __send_routine(self):
        while self.__running:
            try:
                msg = self.__send_queue.get(timeout=5)
                if msg:
                    self.__irc_socket.send((msg + "\r\n").encode(self.__config.config["connection"]["msg_encoding"]))
                    time.sleep(self.__config.config["connection"]["timeout_between_msg"])
            except queue.Empty:
                pass
            except KeyboardInterrupt:
                raise
            except ConnectionResetError:
                self.reconnect()

    def add_chat_msg(self, msg, important=False):
        self.add_raw_msg(("PRIVMSG #%s :%s" % (self.__active_channel, msg)), important)

    def add_raw_msg(self, msg, important=False):
        if important or not self.__config.config["general"]["silent_mode"]\
                or (self.__config.config["general"]["only_silent_in_other_channels"]
                    and self.__active_channel == self.__config.config["connection"]["channel"]):
            self.__send_queue.put(msg)

    def __receive_routine(self):
        buffer = ""
        while self.__running:

            try:
                buffer = "".join((buffer, self.__irc_socket.recv(self.__config.config["connection"]["receive_size_bytes"])
                                  .decode(self.__config.config["connection"]["msg_decoding"])))
            except ConnectionAbortedError:
                if self.__running:
                    self.__handel_reconnect()
                else:
                    return

            if len(buffer) == 0:
                logger.log(logging.WARNING, "CONNECTION LOST")
                self.__handel_reconnect()

            lines = buffer.splitlines(keepends=True)

            if lines:
                if lines[-1].endswith("\r\n"):
                    buffer = ""
                else:
                    buffer = lines.pop()

            for line in lines:
                self.__distribution_manager.add_line(line.rstrip())

    def __handel_reconnect(self):
        if self.__config.config["connection"]["auto_reconnect"]:
            self.reconnect()
        else:
            logger.log(logging.INFO, "AUTO RECONNECT OFF - SHUTTING DOWN")
            self.__running = False
            self.__bot.stop()

    def add_received_msg(self, msg):
        full_msg = (":{0}!{0}@{0}.tmi.twitch.tv PRIVMSG #{1} :{2}"
                    .format(self.__config.config["connection"]["nick_name"].lower(), self.__active_channel, msg))
        self.__distribution_manager.add_line(full_msg)

    def join_channel(self, channel, reconnect=False):
        channel = channel.lower()
        if self.__active_channel:
            self.add_raw_msg("PART #%s" % self.__active_channel, important=True)
            logger.log(logging.INFO, "Left %s" % self.__active_channel)
            self.__active_channel = None
            logger.log(logging.DEBUG, "Cleared receive queue")

        self.add_raw_msg('JOIN #%s' % channel,  important=True)
        self.__active_channel = channel
        logger.log(logging.INFO, "Joined %s" % channel)

        self.__plugin_manager.handle_channel_change(channel)

        if self.__config.config["general"]["join_msg"] and not reconnect:
            self.add_chat_msg(self.__config.config["general"]["join_msg"])

    def reconnect(self):
        logger.log(logging.INFO, "Disconnected -> Attempting to reconnect")
        self.add_raw_msg("PART #%s" % self.__active_channel)
        self.connect(reconnect=True)

    def shutdown(self):
        self.__running = False

    def close(self):
        logger.log(logging.INFO, "Connection closing")
        if self.__config.config["general"]["depart_msg"]:
            self.add_chat_msg(self.__config.config["general"]["depart_msg"])
        self.add_raw_msg("PART #%s" % self.__active_channel)

        self.__running = False
        logger.log(logging.DEBUG, "Waiting for termination")
        if self.__send_thread and self.__send_thread.is_alive():
            self.__send_thread.join()
        self.__irc_socket.shutdown(socket.SHUT_RD)
        self.__irc_socket.close()
        logger.log(logging.DEBUG, "Send Thread -> Closed")
        if self.__receive_thread and self.__receive_thread.is_alive():
            self.__receive_thread.join()
            logger.log(logging.DEBUG, "Receive Thread -> Closed")

    # FIXME change location
    class Color:
        RED = "\033[31m"
        BRIGHT_RED = "\033[31;1m"
        GREEN = "\033[32m"
        BRIGHT_GREEN = "\033[32;1m"
        YELLOW = "\033[33m"
        BRIGHT_YELLOW = "\033[33;1m"
        BLUE = "\033[34m"
        BRIGHT_BLUE = "\033[34;1m"
        MAGENTA = "\033[35m"
        BRIGHT_MAGENTA = "\033[35;1m"
        CYAN = "\033[36m"
        BRIGHT_CYAN = "\033[36;1m"
        WHITE = "\033[37m"
        BRIGHT_WHITE = "\033[37;1m"
        RESET = "\033[0m"


