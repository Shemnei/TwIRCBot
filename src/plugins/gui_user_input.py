import threading
import tkinter
from idlelib import ToolTip
from tkinter import messagebox

import master


class IRCPlugin(master.Plugin):

    def __init__(self):
        super().__init__()
        self.gui_root = None
        self.command_field = None
        self.message_field = None

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
        root.bind("<Return>", self.handle_button)
        root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.gui_root = root

        LC = tkinter.Label(root, text="CMD: ")
        LC.pack(side=tkinter.LEFT)
        EC = tkinter.Entry(root, width=30)
        EC.pack(side=tkinter.LEFT)
        ToolTip.ToolTip(EC, "Enter command")
        self.command_field = EC

        LM = tkinter.Label(root, text="MSG: ")
        LM.pack(side=tkinter.LEFT)
        EM = tkinter.Entry(root, width=30)
        EM.pack(side=tkinter.LEFT)
        ToolTip.ToolTip(EM, "Enter chat massage")
        self.message_field = EM
        BM = tkinter.Button(root, text="Send", command=self.handle_button)
        BM.pack(side=tkinter.RIGHT)

        tkinter.mainloop()

    def on_closing(selt):
        if tkinter.messagebox.askokcancel("Quit", "Do you want to quit?"):
            selt.gui_root.destroy()

    def handle_button(self, event=None):
        msg = self.message_field.get()
        cmd = self.command_field.get()
        if msg:
            self.connection.add_raw_msg(msg)
            self.message_field.delete(0, tkinter.END)
        if cmd:
            self.connection.add_received_msg(cmd)
            self.command_field.delete(0, tkinter.END)
