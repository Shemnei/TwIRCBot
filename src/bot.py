import os
import queue
import re
import socket
import threading
import time
from importlib import util

import cfg
import master


class IRCConnection:

    def __init__(self, config):
        self.config = config
        self.__running = True
        self.__active_channel = None
        self.__send_thread = threading.Thread(target=self.__send_routine, name="send_thread")
        self.__receive_thread = threading.Thread(target=self.__receive_routine, name="receive_thread")
        self.__process_thread = threading.Thread(target=self.__process_routine, name="process_input_thread")

        self.__plugins = None
        self.__irc_socket = None
        self.__send_queue = queue.Queue()
        self.__receive_queue = queue.Queue()

    def connect(self, reconnect=False):
        start_connect = time.time()

        self.__irc_socket = socket.socket()
        self.__irc_socket.connect((self.config["connection"]["server"], self.config["connection"]["port"]))
        print("DEBUG: Connected to %s on %i" % (self.config["connection"]["server"], self.config["connection"]["port"]))
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
        if self.config["connection"]["membership_messages"]:
            req_str += "twitch.tv/membership "
        if self.config["connection"]["tags"]:
            req_str += "twitch.tv/tags "
        if self.config["connection"]["commands"]:
            req_str += "twitch.tv/commands"

        self.__send_queue.put("CAP REQ : %s" % req_str.rstrip())
        self.__send_queue.put('PASS %s' % self.config["connection"]["oauth_token"])
        self.__send_queue.put('NICK %s' % self.config["connection"]["nick_name"])

        self.join_channel(self.config["connection"]["channel"], reconnect=reconnect)

        print("DEBUG: Connection established in %fs" % (time.time() - start_connect))

    def load_plugins(self):
        start_load_plugins = time.time()

        path = self.config["paths"]["plugin_dir"]
        if not os.path.isdir(path):
            os.makedirs(path)

        files = filter(lambda f: f.endswith('.py'), os.listdir(path))
        modules = []
        for file in files:
            spec = util.spec_from_file_location(file[:-3], os.path.join(self.config["paths"]["plugin_dir"], file)) # [:3] cutting .py
            module = util.module_from_spec(spec)
            spec.loader.exec_module(module)
            modules.append(module)

        plugins = list(map(lambda plugin: getattr(plugin, 'IRCPlugin')(), modules))
        loaded = filter(lambda plugin: isinstance(plugin, master.Plugin), plugins)
        self.__plugins = list(loaded)
        not_loaded = filter(lambda plugin: not isinstance(plugin, master.Plugin), plugins)
        for p in not_loaded:
            print("DEBUG: %s not loaded -> needs to be derived from master.Plugin" % p.__module__)

        for p in enumerate(self.__plugins):
            p[1].on_load(self)

        print("DEBUG: Plugins Loaded in %fs" % (time.time() - start_load_plugins))

    def __send_routine(self):
        while self.__running:
            try:
                msg = self.__send_queue.get()
                if msg is not None and msg != "":
                    self.__irc_socket.send((msg + "\r\n").encode(self.config["connection"]["msg_encoding"]))
                    # TODO change sleep time depending on mod or not and add settings
                    time.sleep(self.config["connection"]["timeout_between_msg"])
            except KeyboardInterrupt:
                raise
            except queue.Empty:
                pass

    def add_chat_msg(self, msg, important=False):
        # TODO self.config["connection"]["channel"] for now fine but when reloading cfg or multiple channels not
        self.add_raw_msg(("PRIVMSG #%s :%s" % (self.__active_channel, msg)), important)

    def add_raw_msg(self, msg, important=False):
        if not self.config["general"]["silent_mode"] or important:
            self.__send_queue.put(msg)

    def __receive_routine(self):
        buffer = ""
        while self.__running:
            buffer = "".join((buffer, self.__irc_socket.recv(self.config["connection"]["receive_size_bytes"]).decode(self.config["connection"]["msg_decoding"])))

            if len(buffer) == 0:
                print("CONNECTION LOST")
                if self.config["connection"]["auto_reconnect"]:
                    self.reconnect()
                else:
                    print("AUTO RECONNECT OF - SHUTTING DOWN")
                    self.shutdown()

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
                    .format(self.config["connection"]["nick_name"], self.__active_channel, msg))
        self.__receive_queue.put(full_msg)

    def __process_routine(self):
        while self.__running:
            try:
                line = self.__receive_queue.get()
                if line:
                    for p in self.__plugins:
                        if re.match(p.get_regex(), line):
                            p.cmd(line)
            except KeyboardInterrupt:
                raise
            except queue.Empty:
                pass

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

        for p in self.__plugins:
            p.on_channel_change(self.__active_channel)

        if self.config["general"]["join_msg"] and not self.config["general"]["silent_mode"] and not reconnect:
            self.add_chat_msg(self.config["general"]["join_msg"])

    def reconnect(self):
        print("RECONNECTING")
        self.add_raw_msg("PART #%s" % self.__active_channel)
        self.connect(reconnect=True)

    def shutdown(self):
        self.__running = False

    def close(self):
        print("SHUTTING DOWN")
        if self.config["general"]["depart_msg"] and not self.config["general"]["silent_mode"]:
            self.add_chat_msg(self.config["general"]["depart_msg"])
        self.add_raw_msg("PART #%s" % self.__active_channel)

        self.__running = False

        self.__receive_thread.join()
        print("RECEIVING STOPPED")
        self.__send_thread.join()
        print("SENDING STOPPED")

        for p in enumerate(self.__plugins):
            p[1].on_close()

        self.__irc_socket.close()

    def is_running(self):
        return self.__running

    def get_loaded_plugins(self):
        return self.__plugins[:]

    def nr_loaded_plugins(self):
        return len(self.__plugins)


if __name__ == '__main__':
    # changing windows cmd to utf-8os
    os.system("chcp 65001")
    con = IRCConnection(cfg.config)
    con.load_plugins()
    con.connect()

    # TODO find nicer solution
    while con.is_running():
        time.sleep(5)

    con.close()


