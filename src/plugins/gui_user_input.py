import threading
import tkinter
from idlelib import ToolTip
from tkinter import messagebox

import math

import master


class IRCPlugin(master.Plugin):

    HISTORY_SIZE = 30

    def __init__(self):
        super().__init__()
        self.gui_root = None
        self.command_field = None
        self.message_field = None
        self.command_history = [""]
        self.message_history = [""]
        self.command_index = 0
        self.message_index = 0

    def get_regex(self):
        return r"$ä"

    def cmd(self, line):
        pass

    def on_load(self, bot):
        super().on_load(bot)
        input_thread = threading.Thread(name="user_input_thread", target=self.open_gui)
        input_thread.setDaemon(True)
        input_thread.start()

    def on_channel_change(self, new_channel):
        self.gui_root.wm_title("TwIRC - [Active plugins: %i/%s]" % (len(self.plugin_manager.loaded_plugins), new_channel))

    def open_gui(self):
        root = tkinter.Tk()
        root.wm_title("TwIRC - [Active plugins: %i]" % len(self.plugin_manager.loaded_plugins))
        root.resizable(0, 0)
        root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.gui_root = root

        LC = tkinter.Label(root, text="CMD: ")
        LC.pack(side=tkinter.LEFT)
        EC = tkinter.Entry(root, width=30)
        EC.pack(side=tkinter.LEFT)
        ToolTip.ToolTip(EC, "Enter command")

        EC.bind("<Return>", self.cmd_handle_return)
        EC.bind("<Up>", self.cmd_handle_up)
        EC.bind("<Down>", self.cmd_handle_down)

        self.command_field = EC

        LM = tkinter.Label(root, text="MSG: ")
        LM.pack(side=tkinter.LEFT)
        EM = tkinter.Entry(root, width=30)
        EM.pack(side=tkinter.LEFT)
        ToolTip.ToolTip(EM, "Enter chat massage")

        EM.bind("<Return>", self.msg_handle_return)
        EM.bind("<Up>", self.msg_handle_up)
        EM.bind("<Down>", self.msg_handle_down)

        self.message_field = EM
        tkinter.mainloop()

    def on_closing(selt):
        if tkinter.messagebox.askokcancel("Quit", "Do you want to quit?"):
            selt.gui_root.destroy()

    def msg_handle_return(self, event=None):
        msg = self.message_field.get()
        if msg:
            self.msg_handle_command_history(msg)
            self.connection.add_raw_msg(msg)
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

