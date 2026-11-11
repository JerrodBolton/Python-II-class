# A live clock for the bottom of the sidebar, and our first taste of MULTITHREADING
#
# What is a thread? Normally our program does ONE thing at a time, top to bottom.
# A thread is a second "worker" that runs at the same time as the rest of the app.
# Here the worker's only job is to check the time once a second.
#
# THE GOLDEN RULE of tkinter + threads:
#   Only the main thread (the one running mainloop()) may touch widgets.
#   If a worker thread changes a label directly, the app can crash or glitch at random.
#
# So the two threads talk through a Queue, like passing notes through a mailbox:
#
#   worker thread  --put("10:24:35 AM")-->  [ Queue ]  --get()-->  main thread updates the label
#
# queue.Queue is "thread-safe": both threads can use it at the same time without breaking it.

import threading
import queue
import time
import datetime
import tkinter as tk

import customtkinter as ctk
from theme import colors, font


class Clock(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")

        # Big time on top, smaller date underneath
        self.time_label = ctk.CTkLabel(self, text="", font=font(20, "bold"), text_color=colors["text"], anchor="w")
        self.time_label.pack(fill="x")
        self.date_label = ctk.CTkLabel(self, text="", font=font(11), text_color=colors["text_muted"], anchor="w")
        self.date_label.pack(fill="x")

        # The mailbox the worker thread drops new times into
        self.mailbox = queue.Queue()
        # An Event is an on/off flag that both threads can see. We switch it on to tell the worker to stop.
        self.stop_flag = threading.Event()

        # Create the worker thread. target= is the function it will run.
        # daemon=True means "don't keep the app alive just for this thread": when the window closes, it ends too.
        self.worker = threading.Thread(target=self.tick, daemon=True)
        # start() launches the thread. From here on, tick() runs at the same time as the rest of the app.
        self.worker.start()

        # Start checking the mailbox (this part runs on the main thread)
        self.check_mailbox()

    # ---------- Runs on the WORKER thread ----------
    # It never touches a widget, it only puts text in the mailbox
    def tick(self):
        while not self.stop_flag.is_set():
            now = datetime.datetime.now()
            # %I:%M:%S %p -> "09:24:35 AM", lstrip("0") -> "9:24:35 AM"
            # %A, %B %d, %Y -> "Wednesday, November 11, 2026"
            self.mailbox.put((now.strftime("%I:%M:%S %p").lstrip("0"), now.strftime("%A, %B %d, %Y")))
            # Sleep until the next whole second, so the clock changes right on the second
            time.sleep(1 - (time.time() % 1))

    # ---------- Runs on the MAIN thread ----------
    # Empty the mailbox and show the newest time, then check again in 100 milliseconds
    def check_mailbox(self):
        # If the window is closing, stop the worker and stop checking
        # (winfo_exists() itself can raise TclError once the whole window is gone)
        try:
            if not self.winfo_exists():
                raise tk.TclError
        except tk.TclError:
            self.stop_flag.set()
            return
        try:
            # get_nowait() takes a note out of the mailbox, or raises queue.Empty if there is none
            while True:
                time_text, date_text = self.mailbox.get_nowait()
                self.time_label.configure(text=time_text)
                self.date_label.configure(text=date_text)
        except queue.Empty:
            pass
        # after() schedules this method to run again, without freezing the window
        self.after(100, self.check_mailbox)

    # Stop the worker thread when the clock is removed from the screen
    def destroy(self):
        self.stop_flag.set()
        super().destroy()
