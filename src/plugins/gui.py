import datetime
import io
import json
import threading
import tkinter
import urllib.request
from idlelib import ToolTip
from tkinter import messagebox

from PIL import Image, ImageTk

import master


class IRCPlugin(master.GenericPlugin):
    EMOTE_URL = "http://static-cdn.jtvnw.net/emoticons/v1/%s/1.0"
    GENERIC_BADGE_URL = "http://badges.twitch.tv/v1/badges/global/display"
    CHANNEL_BADGE_URL = "https://api.twitch.tv/kraken/chat/%s/badges?client_id=%s"
    CHEER_URL = "static-cdn.jtvnw.net/bits/light/static/%color/1"
    HISTORY_SIZE = 20

    def __init__(self):
        super().__init__()
        self.gui_root = None
        self.text_field = None
        self.command_field = None
        self.message_field = None

        self.command_history = [""]
        self.message_history = [""]
        self.command_index = 0
        self.message_index = 0
        self.auto_scroll = None

        self.loaded_emotes = {}
        self.loaded_static_badges = {}
        self.loaded_badges = {}

        self.message_display_enabled = None
        self.emote_display_enabled = None
        self.badge_display_enabled = None
        self.nr_loaded_plugins = None

    def get_regex(self):
        if self.message_display_enabled:
            return r"(@.* )?:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :"
        else:
            return r"$ä"

    def cmd(self, message):
        user = message.user[0]
        if message.tags:

            message_parts = ["[" + datetime.datetime.now().strftime("%H:%M:%S") + "] "]

            display_name = message.tags.get("display-name", None)
            if display_name:
                user = display_name

            if message.tags.get("badges", "") and self.badge_display_enabled:
                badges = message.tags["badges"]
                for badge in badges.split(","):
                    if badge.startswith("bits"):
                        message_parts.append("{badge}%s" % badge)
                    else:
                        message_parts.append("{badge}%s" % badge[:-2])
                if len(message_parts) > 1:
                    message_parts.append(" ")

            message_parts.append(user)
            message_parts.append(": ")

            if message.tags.get("emotes", "") and self.emote_display_enabled:
                emotes_str = message.tags.get("emotes", None)
                emotes = self.parse_emotes(emotes_str)
                self.load_emote_if_not_exists(emotes)
                parts = self.parse_msg(message.msg, emotes)
                message_parts.extend(parts)
            else:
                message_parts.append(message.msg)

            self.add_msg(message_parts)
        else:
            self.add_msg(["[" + datetime.datetime.now().strftime("%H:%M:%S") + "] " + user + ": " + message.msg])

    def load_emote_if_not_exists(self, emotes):
        for emote_id in emotes.keys():
            if emote_id == "80393":
                print("GOLDEN KAPPA")
            if emote_id not in self.loaded_emotes:
                try:
                    data = urllib.request.urlopen(self.EMOTE_URL % emote_id).read()
                    stream = io.BytesIO(data)
                    self.loaded_emotes[emote_id] = ImageTk.PhotoImage(Image.open(stream))
                except:
                    # Error during fetch
                    pass

    @staticmethod
    def parse_emotes(emotes_str):
        if emotes_str is None:
            return {}
        emotes = {}
        split = emotes_str.split('/')

        for e in split:
            sp = e.split(':')
            emotes[sp[0]] = sp[1].split(',')

        return emotes

    @staticmethod
    def parse_msg(msg, emotes):
        offset = 0

        merged = []
        [merged.extend(x) for x in emotes.values()]
        merged.sort(key=lambda x: int(x.split('-')[0]))

        for replace_range in merged:
            emote_id = None
            for e_id in emotes.keys():
                if replace_range in emotes[e_id]:
                    emote_id = e_id
                    break
            start, end = replace_range.split('-')
            start = int(start)
            end = int(end)
            rep = "::{emote}%s::" % emote_id
            msg = msg[:start + offset] + rep + msg[end + 1 + offset:]
            offset += start - end - 1 + len(rep)
        return msg.split('::')

    def on_load(self, bot):
        super().on_load(bot)
        self.message_display_enabled = self.config["plugin_settings"]["enable_gui_messages"]
        self.emote_display_enabled = self.config["plugin_settings"]["enable_gui_emotes"]
        self.badge_display_enabled = self.config["plugin_settings"]["enable_gui_badges"]
        self.nr_loaded_plugins = len(self.plugin_manager.get_loaded_plugins())
        gui_thread = threading.Thread(name="user_input_thread", target=self.open_gui)
        gui_thread.setDaemon(True)
        gui_thread.start()

    def on_channel_change(self, new_channel):
        if self.message_display_enabled:
            self.text_field.config(state=tkinter.NORMAL)
            self.text_field.delete("1.0", tkinter.END)
            self.text_field.config(state=tkinter.DISABLED)
        if self.badge_display_enabled:
            t = threading.Thread(target=self.load_badges, args=(new_channel,), name="badges_fetch_thread")
            t.start()
        self.gui_root.wm_title(
            "TwIRC - [Active plugins: %i/%s]" % (self.nr_loaded_plugins, new_channel))

    def __load_static_badges(self):
        try:
            data = urllib.request.urlopen(self.GENERIC_BADGE_URL).read()
            j_data = json.loads(data.decode())

            for k in j_data["badge_sets"].keys():
                for v in j_data["badge_sets"][k]["versions"]:
                        url = j_data["badge_sets"][k]["versions"][v]["image_url_1x"]
                        data = urllib.request.urlopen(url).read()
                        stream = io.BytesIO(data)
                        key = k
                        if k == "mod":
                            key = "moderator"
                        if k == "bits":
                            key += "/" + str(v)
                        self.loaded_static_badges[key] = ImageTk.PhotoImage(Image.open(stream))
        except:
            pass

    def load_badges(self, channel):
        self.loaded_badges.clear()

        if not self.loaded_static_badges:
            self.__load_static_badges()

        self.loaded_badges = self.loaded_static_badges.copy()
        try:
            data = urllib.request.urlopen(self.CHANNEL_BADGE_URL %
                                          (channel, self.bot.get_config_manager()["connection"]["client_id"])).read()
            j_data = json.loads(data.decode())

            for k in j_data.keys():

                url = j_data[k]["image"]
                data = urllib.request.urlopen(url).read()
                stream = io.BytesIO(data)
                if k == "mod":
                    k = "moderator"
                self.loaded_badges[k] = ImageTk.PhotoImage(Image.open(stream))

        except:
            pass

    def open_gui(self):
        root = tkinter.Tk()
        root.wm_title("TwIRC - [Active plugins: %i]" % self.nr_loaded_plugins)
        root.resizable(0, 0)
        root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.gui_root = root

        if self.message_display_enabled:
            chat_text = tkinter.Text(wrap=tkinter.WORD)
            chat_text.config(state=tkinter.DISABLED)
            chat_text.grid(row=0, column=0, rowspan=8, columnspan=9)
            self.text_field = chat_text

        command_label = tkinter.Label(root, text="CMD: ")
        command_label.grid(row=9, column=0)
        command_entry = tkinter.Entry(root, width=30)
        command_entry.grid(row=9, column=1, columnspan=3)
        ToolTip.ToolTip(command_entry, "Enter command")

        command_entry.bind("<Return>", self.cmd_handle_return)
        command_entry.bind("<Up>", self.cmd_handle_up)
        command_entry.bind("<Down>", self.cmd_handle_down)

        self.command_field = command_entry

        message_label = tkinter.Label(root, text="MSG: ")
        message_label.grid(row=9, column=4)
        message_entry = tkinter.Entry(root, width=30)
        message_entry.grid(row=9, column=5, columnspan=3)
        ToolTip.ToolTip(message_entry, "Enter chat massage")

        message_entry.bind("<Return>", self.msg_handle_return)
        message_entry.bind("<Up>", self.msg_handle_up)
        message_entry.bind("<Down>", self.msg_handle_down)

        self.message_field = message_entry

        if self.message_display_enabled:
            self.auto_scroll = tkinter.IntVar()
            auto_scroll_checkbox = tkinter.Checkbutton(root, text="AutoScroll", variable=self.auto_scroll,
                                                       onvalue=1, offvalue=0)
            auto_scroll_checkbox.toggle()
            auto_scroll_checkbox.grid(row=9, column=8)

        tkinter.mainloop()

    def add_msg(self, msg):
        self.text_field.config(state=tkinter.NORMAL)
        for part in msg:
            if part.startswith("{emote}"):
                emote_id = part.replace("{emote}", "")
                try:
                    self.text_field.image_create(tkinter.END, image=self.loaded_emotes[emote_id])
                except:
                    # emote not there
                    pass
            elif part.startswith("{badge}"):
                badge_id = part.replace("{badge}", "")
                try:
                    self.text_field.image_create(tkinter.END, image=self.loaded_badges[badge_id])
                except:
                    # badge not there
                    pass
            else:
                try:
                    self.text_field.insert(tkinter.END, part)
                except:
                    print("DEBUG: GUI UNEXPECTED CHAR: %s" % part)
        self.text_field.insert(tkinter.END, "\n")
        if self.auto_scroll.get() == 1:
            self.text_field.see(tkinter.END)
        self.text_field.config(state=tkinter.DISABLED)

    def on_closing(self):
        if tkinter.messagebox.askokcancel("Quit", "Do you want to hide the GUI ?"):
            self.gui_root.withdraw()

    def msg_handle_return(self, event=None):
        msg = self.message_field.get()
        if msg:
            self.msg_handle_command_history(msg)
            self.connection.add_chat_msg(msg)
            self.message_field.delete(0, tkinter.END)

    def msg_handle_command_history(self, msg):
        if len(self.message_history) > IRCPlugin.HISTORY_SIZE:
            self.message_history.pop()
        self.message_history.insert(1, msg)
        self.message_index = 0

    def msg_handle_up(self, event=None):
        self.message_index += 1
        self.message_index = min(self.message_index, len(self.message_history) - 1)
        self.message_field.delete(0, tkinter.END)
        self.message_field.insert(0, self.message_history[self.message_index])

    def msg_handle_down(self, event=None):
        self.message_index -= 1
        self.message_index = max(self.message_index, 0)
        self.message_field.delete(0, tkinter.END)
        self.message_field.insert(0, self.message_history[self.message_index])

    def cmd_handle_return(self, event=None):
        cmd = self.command_field.get()
        if cmd:
            self.cmd_handle_command_history(cmd)
            self.connection.add_received_msg(cmd)
            self.command_field.delete(0, tkinter.END)

    def cmd_handle_command_history(self, cmd):
        if len(self.command_history) > IRCPlugin.HISTORY_SIZE:
            self.command_history.pop()
        self.command_history.insert(1, cmd)
        self.command_index = 0

    def cmd_handle_up(self, event=None):
        self.command_index += 1
        self.command_index = min(self.command_index, len(self.command_history) - 1)
        self.command_field.delete(0, tkinter.END)
        self.command_field.insert(0, self.command_history[self.command_index])

    def cmd_handle_down(self, event=None):
        self.command_index -= 1
        self.command_index = max(self.command_index, 0)
        self.command_field.delete(0, tkinter.END)
        self.command_field.insert(0, self.command_history[self.command_index])