# VORTEXA - a local LLM desktop app built with CustomTkinter and llama_cpp
#
# How the files fit together:
#   main.py          <- you are here. Builds the window and connects the GUI to the LLM
#   llm.py           <- everything that talks to the model (load, prompt template, generate)
#   theme.py         <- reads assets/theme.json (our Cosmic Gateway colors and fonts)
#   logo.py          <- the round orb logo and the glowing VORTEXA name
#   icons.py         <- loads and colors the icons in assets/icons
#   ui/sidebar.py    <- logo, navigation buttons, conversation list
#   ui/header.py     <- model name, status and the stat cards
#   ui/chat_view.py  <- the scrolling list of message cards
#   ui/input_bar.py  <- the message box, toggles, token counter and Send button
import time
import datetime
# We still use tkinter for one thing: catching its error if the window is closed mid-answer
import tkinter as tk
# customtkinter gives our app a modern look, it is built on top of tkinter
import customtkinter as ctk

import llm
from theme import theme, colors, font
from ui.sidebar import Sidebar
from ui.header import ModelHeader
from ui.chat_view import ChatView
from ui.input_bar import InputBar

# Create a version number to keep track of the version of the application and for github
version = "1.10"

# Let's get todays date and time, we will use this to display in the GUI
todays_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# The current time like "10:24 AM", shown on each message
def time_now():
    return datetime.datetime.now().strftime("%I:%M %p").lstrip("0")


# Our whole app is one class. VortexaApp IS the main window (it "inherits" from ctk.CTk),
# so inside the class "self" is the window, the same thing your old code called root.
class VortexaApp(ctk.CTk):
    def __init__(self):
        # Set the look of our app, "dark", "light" or "system" (follows your Mac's setting)
        ctk.set_appearance_mode(theme.get("appearance_mode", "dark"))
        ctk.set_default_color_theme(theme.get("button_color_theme", "blue"))
        super().__init__(fg_color=colors["background"])

        self.title("VORTEXA - v" + version + " - " + todays_date)
        self.geometry(theme.get("window_size", "1360x880"))
        self.minsize(*theme.get("window_min_size", [1100, 720]))

        # Our conversations live in memory for now (saving them to disk is a later milestone)
        # Each one looks like: {"id": 1, "title": "...", "time": "Today, 10:24 AM", "messages": [...]}
        self.conversations = []
        self.current_conversation = None
        self.next_conversation_id = 1
        self.is_generating = False

        self.build_layout()
        self.new_chat()
        self.show_page("Chat")

        # Draw the window FIRST, then load the model, so you see the app while the model loads
        self.input_bar.set_busy(True)
        self.after(200, self.load_model)

    # ---------- Building the window ----------
    def build_layout(self):
        # grid() splits the window into a table. Column 0 = sidebar, column 1 = everything else.
        # weight=1 means column 1 / row 0 get all the extra space when the window grows.
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = Sidebar(self, on_nav=self.show_page, on_new_chat=self.new_chat,
                               on_select_conversation=self.open_conversation)
        self.sidebar.grid(row=0, column=0, sticky="ns", padx=(16, 8), pady=16)

        main_area = ctk.CTkFrame(self, fg_color="transparent")
        main_area.grid(row=0, column=1, sticky="nsew", padx=(8, 16), pady=16)

        self.header = ModelHeader(main_area)
        self.header.pack(fill="x", pady=(0, 12))

        # Each sidebar button shows a "page". The Chat page holds the chat and the input bar.
        self.pages = {}
        chat_page = ctk.CTkFrame(main_area, fg_color="transparent")
        self.chat_view = ChatView(chat_page)
        self.chat_view.pack(fill="both", expand=True)
        self.input_bar = InputBar(chat_page, on_send=self.send_message,
                                  count_tokens=llm.count_tokens, context_size=llm.context_size)
        self.input_bar.pack(fill="x", pady=(12, 0))
        self.pages["Chat"] = chat_page

        # The other pages are simple placeholders until we build them in later milestones
        for page_name in ["Models", "Knowledge Base", "Prompts", "RAG & Documents", "Settings"]:
            page = ctk.CTkFrame(main_area, fg_color=colors["panel"], corner_radius=22,
                                border_width=1, border_color=colors["panel_border"])
            ctk.CTkLabel(page, text=page_name, font=font(26, "bold"), text_color=colors["text"]).place(relx=0.5, rely=0.45, anchor="center")
            ctk.CTkLabel(page, text="Coming in a later milestone", font=font(15),
                         text_color=colors["text_muted"]).place(relx=0.5, rely=0.52, anchor="center")
            self.pages[page_name] = page

    # Hide every page, then show the one we clicked
    def show_page(self, page_name):
        for page in self.pages.values():
            page.pack_forget()
        self.pages[page_name].pack(fill="both", expand=True)
        self.sidebar.set_active_page(page_name)

    # ---------- Loading the model ----------
    def load_model(self):
        llm.load_model()
        self.header.set_model_info(llm.model_info())
        self.header.set_status("connected")
        self.input_bar.set_busy(False)

    # ---------- Conversations ----------
    def new_chat(self):
        if self.is_generating:
            return
        conversation = {"id": self.next_conversation_id, "title": "New Chat",
                        "time": "Today, " + time_now(), "messages": []}
        self.next_conversation_id += 1
        # insert(0, ...) puts the newest conversation at the top of the list
        self.conversations.insert(0, conversation)
        self.open_conversation(conversation["id"])

    def open_conversation(self, conversation_id):
        if self.is_generating:
            return
        self.current_conversation = next(c for c in self.conversations if c["id"] == conversation_id)
        # Redraw the chat from the saved messages
        self.chat_view.clear()
        for message in self.current_conversation["messages"]:
            card = self.chat_view.add_message(message["role"], message["text"], message["time"])
            if message["role"] == "ai":
                card.show_completed(message["tokens"], message["seconds"])
        self.sidebar.set_conversations(self.conversations, conversation_id)
        self.show_page("Chat")

    # ---------- Sending a message and streaming the answer ----------
    def send_message(self, user_text):
        if self.is_generating or llm.model is None:
            return
        self.is_generating = True
        self.input_bar.set_busy(True)
        conversation = self.current_conversation

        # The first message becomes the conversation's title in the sidebar
        if not conversation["messages"]:
            conversation["title"] = user_text if len(user_text) <= 22 else user_text[:21].rstrip() + "…"
            self.sidebar.set_conversations(self.conversations, conversation["id"])

        conversation["messages"].append({"role": "user", "text": user_text, "time": time_now()})
        self.chat_view.add_message("user", user_text, time_now())

        # Make an empty AI card, then fill it one token at a time
        ai_time = time_now()
        card = self.chat_view.add_message("ai", "", ai_time)
        start_time = time.time()
        token_count = 0
        try:
            for piece in llm.stream_response(user_text):
                token_count += 1
                card.append_text(piece)
                card.show_generating(token_count, time.time() - start_time)
                self.chat_view.scroll_to_bottom()
                # Now let our GUI update events (same idea as root.update() in your original code)
                self.update()
        except tk.TclError:
            # The window was closed while the model was still answering
            return

        seconds = time.time() - start_time
        card.show_completed(token_count, seconds)
        conversation["messages"].append({"role": "ai", "text": card.body.cget("text"), "time": ai_time,
                                         "tokens": token_count, "seconds": seconds})
        self.is_generating = False
        self.input_bar.set_busy(False)


# App start here
if __name__ == "__main__":
    app = VortexaApp()
    # Must have this to run our app
    app.mainloop()
