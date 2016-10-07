import datetime
import os
import threading
import tkinter
from tkinter import messagebox
import urllib.request
from idlelib import ToolTip

from PIL import Image, ImageTk
import time

import master


class IRCPlugin(master.GenericPlugin):
    URL = "http://static-cdn.jtvnw.net/emoticons/v1/%s/1.0"
    EMOTE_DIR = "emotes"
    HISTORY_SIZE = 20

    def __init__(self):
        super().__init__()
        self.gui_root = None
        self.text_field = None
        self.loaded_emotes = {}
        self.command_field = None
        self.message_field = None
        self.command_history = [""]
        self.message_history = [""]
        self.command_index = 0
        self.message_index = 0
        self.auto_scroll = None

    def get_regex(self):
        return r"(@.* )?:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :"

    def cmd(self, message):
        user = message.user[0]
        if message.tags and message.tags.get("emotes", ""):
            user = message.tags.get("display-name", user)
            emotes_str = message.tags.get("emotes", None)
            emotes = self.parse_emotes(emotes_str)
            self.load_emote_if_not_exists(emotes)
            parts = self.parse_msg(message.msg, emotes)
            parts.insert(0, "[" + datetime.datetime.now().strftime("%H:%M:%S") + "] " + user + ": ")
            self.add_msg(parts)
        else:
            self.add_msg(["[" + datetime.datetime.now().strftime("%H:%M:%S") + "] " + user + ": " + message.msg])

    def load_emote_if_not_exists(self, emotes):
        for emote_id in emotes.keys():
            if not os.path.isfile(os.path.join(IRCPlugin.EMOTE_DIR, emote_id + ".png")):
                urllib.request.urlretrieve(IRCPlugin.URL % emote_id, os.path.join(IRCPlugin.EMOTE_DIR, emote_id + ".png"))
            if emote_id not in self.loaded_emotes:
                self.loaded_emotes[emote_id] = ImageTk.PhotoImage(Image.open(os.path.join(IRCPlugin.EMOTE_DIR, emote_id + ".png")))

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

    def load_existing_emotes(self):
        loaded_emotes = 0
        some_dir = os.path.join(IRCPlugin.EMOTE_DIR)
        assert os.path.isdir(some_dir)
        num_sep = some_dir.count(os.path.sep)
        for root, dirs, files in os.walk(some_dir):
            for file in files:
                if file.endswith(".png"):
                    loaded_emotes += 1
                    name = os.path.splitext(file)[0]
                    self.loaded_emotes[name] = ImageTk.PhotoImage(Image.open(os.path.join(IRCPlugin.EMOTE_DIR, file)))
            num_sep_this = root.count(os.path.sep)
            if num_sep + 1 <= num_sep_this:
                del dirs[:]
        print("Loaded Emotes: %i" % loaded_emotes)

    def on_load(self, bot):
        super().on_load(bot)
        if not os.path.isdir(IRCPlugin.EMOTE_DIR):
            os.makedirs(IRCPlugin.EMOTE_DIR)
        gui_thread = threading.Thread(name="user_input_thread", target=self.open_gui)
        gui_thread.setDaemon(True)
        gui_thread.start()
        self.load_existing_emotes()

    def on_channel_change(self, new_channel):
        self.text_field.delete("1.0", tkinter.END)
        self.gui_root.wm_title(
            "TwIRC - [Active plugins: %i/%s]" % (len(self.plugin_manager.loaded_plugins), new_channel))

    def open_gui(self):
        root = tkinter.Tk()
        root.wm_title("TwIRC - [Active plugins: %i]" % len(self.plugin_manager.loaded_plugins))
        root.resizable(0, 0)
        root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.gui_root = root

        TW = tkinter.Text(wrap=tkinter.WORD)
        TW.config(state=tkinter.DISABLED)
        TW.grid(row=0, column=0, rowspan=8, columnspan=9)
        self.text_field = TW

        LC = tkinter.Label(root, text="CMD: ")
        LC.grid(row=9, column=0)
        EC = tkinter.Entry(root, width=30)
        EC.grid(row=9, column=1, columnspan=3)
        ToolTip.ToolTip(EC, "Enter command")

        EC.bind("<Return>", self.cmd_handle_return)
        EC.bind("<Up>", self.cmd_handle_up)
        EC.bind("<Down>", self.cmd_handle_down)

        self.command_field = EC

        LM = tkinter.Label(root, text="MSG: ")
        LM.grid(row=9, column=4)
        EM = tkinter.Entry(root, width=30)
        EM.grid(row=9, column=5, columnspan=3)
        ToolTip.ToolTip(EM, "Enter chat massage")

        EM.bind("<Return>", self.msg_handle_return)
        EM.bind("<Up>", self.msg_handle_up)
        EM.bind("<Down>", self.msg_handle_down)

        self.message_field = EM

        self.auto_scroll = tkinter.IntVar()
        CB = tkinter.Checkbutton(root, text="AutoScroll", variable=self.auto_scroll, onvalue=1, offvalue=0)
        CB.toggle()
        CB.grid(row=9, column=8)

        tkinter.mainloop()

    def add_msg(self, msg):
        self.text_field.config(state=tkinter.NORMAL)
        for parts in msg:
            if parts.startswith("{emote}"):
                emote_id = parts.replace("{emote}", "")
                self.text_field.image_create(tkinter.END, image=self.loaded_emotes[emote_id])
            else:
                try:
                    self.text_field.insert(tkinter.END, parts)
                except:
                    pass
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