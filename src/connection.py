import queue
import re
import socket
import ssl
import threading
import time


class IRCConnection:

    def __init__(self, bot):
        self.__bot = bot
        self.__config = bot.get_config_manager()
        self.__running = False
        self.__active_channel = None
        self.__send_thread = threading.Thread(target=self.__send_routine, name="send_thread")
        self.__receive_thread = threading.Thread(target=self.__receive_routine, name="receive_thread")
        self.__process_thread = threading.Thread(target=self.__process_routine, name="process_input_thread")

        self.__plugin_manager = None
        self.__irc_socket = None
        self.__send_queue = queue.Queue()
        self.__receive_queue = queue.Queue()

    def connect(self, reconnect=False):
        self.__running = True
        self.__plugin_manager = self.__bot.get_plugin_manager()
        start_connect = time.time()

        tmp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        if self.__config["connection"]["ssl"]:
            self.__irc_socket = ssl.wrap_socket(tmp)
        else:
            self.__irc_socket = tmp

        self.__irc_socket.connect((self.__config["connection"]["server"], self.__config["connection"]["port"]))
        print("DEBUG: Connected to %s on %i" % (self.__config["connection"]["server"], self.__config["connection"]["port"]))
        if not self.__send_thread.is_alive():
            self.__send_thread.start()
            print("DEBUG: Send Thread started")
        if not self.__receive_thread.is_alive():
            self.__receive_thread.start()
            print("DEBUG: Receive Thread started")
        if not self.__process_thread.is_alive():
            self.__process_thread.start()
            print("DEBUG: Process Thread started")

        req_str = ""
        if self.__config["connection"]["membership_messages"]:
            req_str += "twitch.tv/membership "
        if self.__config["connection"]["tags"]:
            req_str += "twitch.tv/tags "
        if self.__config["connection"]["commands"]:
            req_str += "twitch.tv/commands"

        self.__send_queue.put("CAP REQ : %s" % req_str.rstrip())
        self.__send_queue.put('PASS %s' % self.__config["connection"]["oauth_token"])
        self.__send_queue.put('NICK %s' % self.__config["connection"]["nick_name"])

        self.join_channel(self.__config["connection"]["channel"], reconnect=reconnect)

        print("DEBUG: Connection established in %fms" % ((time.time() - start_connect)*1000))

    def __send_routine(self):
        while self.__running:
            try:
                msg = self.__send_queue.get(timeout=5)
                if msg:
                    # FIXME: ConnectionResetError -> Reconnect
                    self.__irc_socket.send((msg + "\r\n").encode(self.__config["connection"]["msg_encoding"]))
                    # TODO change sleep time depending on mod or not and add settings
                    time.sleep(self.__config["connection"]["timeout_between_msg"])
            except KeyboardInterrupt:
                raise
            except queue.Empty:
                pass

    def add_chat_msg(self, msg, important=False):
        self.add_raw_msg(("PRIVMSG #%s :%s" % (self.__active_channel, msg)), important)

    def add_raw_msg(self, msg, important=False):
        if important or not self.__config["general"]["silent_mode"] or (self.__config["general"]["only_silent_in_other_channels"] and self.__active_channel == self.__config["connection"]["channel"]):
            self.__send_queue.put(msg)

    def __receive_routine(self):
        buffer = ""
        while self.__running:
            buffer = "".join((buffer, self.__irc_socket.recv(self.__config["connection"]["receive_size_bytes"])
                              .decode(self.__config["connection"]["msg_decoding"])))

            if len(buffer) == 0:
                print("CONNECTION LOST")
                if self.__config["connection"]["auto_reconnect"]:
                    self.reconnect()
                else:
                    print("AUTO RECONNECT OF - SHUTTING DOWN")
                    self.__running = False
                    self.__bot.stop()

            lines = buffer.splitlines(keepends=True)

            if lines:
                if lines[-1].endswith("\r\n"):
                    buffer = ""
                else:
                    buffer = lines.pop()

            for line in lines:
                self.__receive_queue.put(line.rstrip())

    def add_received_msg(self, msg):
        full_msg = (":{0}!{0}@{0}.tmi.twitch.tv PRIVMSG #{1} :{2}"
                    .format(self.__config["connection"]["nick_name"], self.__active_channel, msg))
        self.__receive_queue.put(full_msg)

    def __process_routine(self):
        while self.__running:
            try:
                line = self.__receive_queue.get(timeout=5)
                if line:
                    for p in self.__plugin_manager.loaded_plugins:
                        if re.match(p.get_regex(), line):
                            p.cmd(line)
            except queue.Empty:
                pass
            except KeyboardInterrupt:
                raise

    def join_channel(self, channel, reconnect=False):
        if self.__active_channel:
            self.add_raw_msg("PART #%s" % self.__active_channel, important=True)
            print("DEBUG: Left %s" % self.__active_channel)
            self.__active_channel = None
            with self.__receive_queue.mutex:
                self.__receive_queue.queue.clear()
            print("DEBUG: Cleared receive queue")

        self.add_raw_msg('JOIN #%s' % channel,  important=True)
        self.__active_channel = channel
        print("DEBUG: Joined %s" % channel)

        for p in self.__plugin_manager.loaded_plugins:
            p.on_channel_change(self.__active_channel)

        if self.__config["general"]["join_msg"] and not reconnect:
            self.add_chat_msg(self.__config["general"]["join_msg"])

    def reconnect(self):
        print("RECONNECTING")
        self.add_raw_msg("PART #%s" % self.__active_channel)
        self.connect(reconnect=True)

    def shutdown(self):
        self.__running = False

    def close(self):
        print("DEBUG: Connection closing")
        if self.__config["general"]["depart_msg"]:
            self.add_chat_msg(self.__config["general"]["depart_msg"])
        self.add_raw_msg("PART #%s" % self.__active_channel)

        self.__running = False

        self.__receive_thread.join()
        print("DEBUG: Receive Thread stopped")
        self.__send_thread.join()
        print("DEBUG: Send Thread stopped")
        self.__process_thread.join()
        print("DEBUG: Process Thread stopped")

        self.__irc_socket.close()

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

    @staticmethod
    def parse_tags(tag_str):
        tag_str = tag_str.strip()
        tag_str = tag_str.lstrip('@')
        tags = {}
        for tag_c in tag_str.split(";"):
            i = tag_c.find("=")
            tags[tag_c[:i]] = tag_c[i + 1:]
        return tags
