import os
import queue
import re
import socket
import threading
import time
from importlib import util

import collections

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
            spec = util.spec_from_file_location(file[:-3], os.path.join(self.config["paths"]["plugin_dir"], file))
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
            buffer = "".join((buffer, self.__irc_socket.recv(self.config["connection"]["receive_size_bytes"])
                              .decode(self.config["connection"]["msg_decoding"])))

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

    # TODO: MOVE
    class TagCompound:
        def __init__(self, tag_str):
            self.tag_str = tag_str
            self.tag_str = self.tag_str.lstrip('@')
            self.tag_str += " "

            self.tags = {}

        def get_badges(self):
            if "badges" not in self.tags.keys():
                badges = re.search(r"badges=([\w_,\/]*)[; ]", self.tag_str)
                if badges:
                    badges = (badges.group(1) or "").split(",")
                self.tags["badges"] = badges
                return badges
            return self.tags["badges"]

        def get_color(self):
            if "color" not in self.tags.keys():
                color = re.search(r"color=(#[\da-fA-F]{6})?[; ]", self.tag_str)
                if color:
                    color = color.group(1)
                self.tags["color"] = color
                return color
            return self.tags["color"]

        def get_displayname(self):
            if "display-name" not in self.tags.keys():
                display_name = re.search(r"display-name=([a-zA-Z0-9_]*)[; ]", self.tag_str)
                if display_name:
                    display_name = display_name.group(1)
                self.tags["display-name"] = display_name
                return display_name
            return self.tags["display-name"]

        def get_emotes(self):
            if "emotes" not in self.tags.keys():
                emotes = re.search(r"emotes=([\d:\/,-]*)[; ]", self.tag_str)
                if emotes:
                    emotes = (emotes.group(1) or "").split("/")
                self.tags["emotes"] = emotes
                return emotes
            return self.tags["emotes"]

        def get_id(self):
            if "id" not in self.tags.keys():
                m_id = re.search(r";id=([\w\d-]*)[; ]", self.tag_str)
                if m_id:
                    m_id = m_id.group(1)
                self.tags["id"] = m_id
                return m_id
            return self.tags["id"]

        def get_mod(self):
            if "mod" not in self.tags.keys():
                mod = re.search(r"mod=(0|1)?[; ]", self.tag_str)
                if mod:
                    mod = mod.group(1) or "0"
                self.tags["mod"] = mod
                return mod
            return self.tags["mod"]

        def get_subscriber(self):
            if "subscriber" not in self.tags.keys():
                subscriber = re.search(r"subscriber=(0|1)?[; ]", self.tag_str)
                if subscriber:
                    subscriber = subscriber.group(1) or "0"
                self.tags["subscriber"] = subscriber
                return subscriber
            return self.tags["subscriber"]

        def get_turbo(self):
            if "turbo" not in self.tags.keys():
                turbo = re.search(r"turbo=(0|1)?[; ]", self.tag_str)
                if turbo:
                    turbo = turbo.group(1) or "0"
                self.tags["turbo"] = turbo
                return turbo
            return self.tags["turbo"]

        def get_roomid(self):
            if "room-id" not in self.tags.keys():
                room_id = re.search(r"room-id=(\d*)[; ]", self.tag_str)
                if room_id:
                    room_id = room_id.group(1)
                self.tags["room-id"] = room_id
                return room_id
            return self.tags["room-id"]

        def get_userid(self):
            if "user-id" not in self.tags.keys():
                user_id = re.search(r"user-id=(\d*)[; ]", self.tag_str)
                if user_id:
                    user_id = user_id.group(1)
                self.tags["user-id"] = user_id
                return user_id
            return self.tags["user-id"]

        def get_usertype(self):
            if "user-type" not in self.tags.keys():
                user_type = re.search(r"user-type=([\w_]*)[; ]", self.tag_str)
                if user_type:
                    user_type = (user_type.group(1) or "").split(",")
                self.tags["user-type"] = user_type
                return user_type
            return self.tags["user-type"]

        def get_bits(self):
            if "bits" not in self.tags.keys():
                bits = re.search(r"bits=([\d]*)[; ]", self.tag_str)
                if bits:
                    bits = bits.group(1)
                self.tags["bits"] = bits
                return bits
            return self.tags["bits"]

        def get_sentts(self):
            if "sent-ts" not in self.tags.keys():
                sent_ts = re.search(r"sent-ts=([\d]*)[; ]", self.tag_str)
                if sent_ts:
                    sent_ts = sent_ts.group(1)
                self.tags["sent-ts"] = sent_ts
                return sent_ts
            return self.tags["sent-ts"]

        def get_tmisentts(self):
            if "tmi-sent-ts" not in self.tags.keys():
                tmi_sent_ts = re.search(r"tmi-sent-ts=([\d]*)[; ]", self.tag_str)
                if tmi_sent_ts:
                    tmi_sent_ts = tmi_sent_ts.group(1)
                self.tags["tmi-sent-ts"] = tmi_sent_ts
                return tmi_sent_ts
            return self.tags["tmi-sent-ts"]

        def get_emotesets(self):
            if "emote-sets" not in self.tags.keys():
                emote_sets = re.search(r"emote-sets=([\d,]*)[; ]", self.tag_str)
                if emote_sets:
                    emote_sets = (emote_sets.group(1) or "").split(",")
                self.tags["emote-sets"] = emote_sets
                return emote_sets
            return self.tags["emote-sets"]

        def get_broadcasterlang(self):
            if "broadcaster-lang" not in self.tags.keys():
                broadcaster_lang = re.search(r"broadcaster-lang=([\w-]*)[; ]", self.tag_str)
                if broadcaster_lang:
                    broadcaster_lang = broadcaster_lang.group(1)
                self.tags["broadcaster-lang"] = broadcaster_lang
                return broadcaster_lang
            return self.tags["broadcaster-lang"]

        def get_r9k(self):
            if "r9k" not in self.tags.keys():
                r9k = re.search(r"r9k=(0|1)?[; ]", self.tag_str)
                if r9k:
                    r9k = r9k.group(1)
                self.tags["r9k"] = r9k
                return r9k
            return self.tags["r9k"]

        def get_subsonly(self):
            if "subs-only" not in self.tags.keys():
                subs_only = re.search(r"subs-only=(0|1)?[; ]", self.tag_str)
                if subs_only:
                    subs_only = subs_only.group(1)
                self.tags["subs-only"] = subs_only
                return subs_only
            return self.tags["subs-only"]

        def get_slow(self):
            if "slow" not in self.tags.keys():
                slow = re.search(r"slow=(\d*)[; ]", self.tag_str)
                if slow:
                    slow = slow.group(1)
                self.tags["slow"] = slow
                return slow
            return self.tags["slow"]

        def get_msgid(self):
            if "msg-id" not in self.tags.keys():
                msg_id = re.search(r"msg-id=(\w*)[; ]", self.tag_str)
                if msg_id:
                    msg_id = msg_id.group(1)
                self.tags["msg-id"] = msg_id
                return msg_id
            return self.tags["msg-id"]

        def get_msgparammonths(self):
            if "msg-param-months" not in self.tags.keys():
                msg_param_months = re.search(r"msg-param-months=(\d*)[; ]", self.tag_str)
                if msg_param_months:
                    msg_param_months = msg_param_months.group(1)
                self.tags["msg-param-months"] = msg_param_months
                return msg_param_months
            return self.tags["msg-param-months"]

        def get_systemmsg(self):
            if "system-msg" not in self.tags.keys():
                system_msg = re.search(r"system-msg=(.[^; ]*)[; ]", self.tag_str)
                if system_msg:
                    system_msg = system_msg.group(1)
                self.tags["system-msg"] = system_msg
                return system_msg
            return self.tags["system-msg"]

        def get_login(self):
            if "login" not in self.tags.keys():
                login = re.search(r"login=([a-zA-Z0-9_]*)[; ]", self.tag_str)
                if login:
                    login = login.group(1)
                self.tags["login"] = login
                return login
            return self.tags["login"]

        def get_banduration(self):
            if "ban-duration" not in self.tags.keys():
                ban_duration = re.search(r"ban-duration=(\d*)[; ]", self.tag_str)
                if ban_duration:
                    ban_duration = ban_duration.group(1)
                self.tags["ban-duration"] = ban_duration
                return ban_duration
            return self.tags["ban-duration"]

        def get_banreason(self):
            if "ban-reason" not in self.tags.keys():
                ban_reason = re.search(r"ban-reason=([a-zA-Z0-9_]*)[; ]", self.tag_str)
                if ban_reason:
                    ban_reason = ban_reason.group(1)
                self.tags["ban-reason"] = ban_reason
                return ban_reason
            return self.tags["ban-reason"]

if __name__ == '__main__':

    con = IRCConnection(cfg.config)
    con.load_plugins()
    con.connect()

    # TODO find nicer solution
    while con.is_running():
        try:
            time.sleep(5)
        except KeyboardInterrupt:
            raise
    con.close()
