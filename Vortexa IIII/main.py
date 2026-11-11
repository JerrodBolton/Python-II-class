# VORTEXA - a local LLM desktop app built with CustomTkinter and llama_cpp
#
# How the files fit together:
#   main.py          <- you are here. Builds the window and connects the GUI to the LLM
#   llm.py           <- everything that talks to the model (load, switch models, generate)
#   hub.py           <- finds and downloads models from Hugging Face
#   theme.py         <- reads assets/theme.json (our Cosmic Gateway colors and fonts)
#   logo.py          <- the round orb logo and the glowing VORTEXA name
#   icons.py         <- loads and colors the icons in assets/icons
#   ui/sidebar.py    <- logo, navigation buttons, conversation list
#   ui/clock.py      <- the live clock in the bottom left (our first background thread)
#   ui/header.py     <- model name, status and the stat cards
#   ui/chat_view.py  <- the scrolling list of message cards
#   ui/input_bar.py  <- the message box, toggles, token counter and Send button
#   ui/add_model_dialog.py <- the window for downloading a model from Hugging Face
#
# To run the app: open a terminal in the Vortexa folder, then
#   source .venv/bin/activate
#   python main.py

# We use time to measure how long the model takes to answer (for the "2.4s" and "tokens/s")
import time
# Import a library to get the current date and time
import datetime
# threading lets the model answer in a background "worker" thread, so the window never freezes
import threading
# queue is the thread-safe "mailbox" the worker uses to send pieces of the answer to the window
import queue
# customtkinter gives our app a modern look, it is built on top of tkinter
import customtkinter as ctk

# Our own files! "import llm" lets us write llm.load_model(), llm.stream_response() and so on
import llm
from theme import theme, colors
# Each part of the screen is a class in the ui folder
from ui.sidebar import Sidebar
from ui.header import ModelHeader
from ui.chat_view import ChatView
from ui.input_bar import InputBar
from ui.add_model_dialog import AddModelDialog

# Create a version number to keep track of the version of the application and for github
version = "1.10"

# Let's get todays date and time, we will use this to display in the GUI
todays_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# The current time like "10:24 AM", shown on each message
# %I = hour (01-12), %M = minutes, %p = AM or PM. lstrip("0") turns "09:12 AM" into "9:12 AM"
def time_now():
    return datetime.datetime.now().strftime("%I:%M %p").lstrip("0")


# Our whole app is one class. VortexaApp IS the main window (it "inherits" from ctk.CTk),
# so inside the class "self" is the window, the same thing your old code called root.
class VortexaApp(ctk.CTk):
    # __init__ runs once, when the app starts. It sets everything up.
    def __init__(self):
        # Set the look of our app, "dark", "light" or "system" (follows your Mac's setting)
        ctk.set_appearance_mode(theme.get("appearance_mode", "dark"))
        # Set the default color of our widgets. Our own colors from theme.json are used on top of this.
        ctk.set_default_color_theme(theme.get("button_color_theme", "blue"))
        # super().__init__ creates the actual window (the ctk.CTk part of our class)
        super().__init__(fg_color=colors["background"])

        # Set the title of our app
        self.title("VORTEXA - v" + version + " - " + todays_date)
        # The starting window size, like "1360x880" (width x height)
        self.geometry(theme.get("window_size", "1360x880"))
        # The smallest the window is allowed to get. The * "unpacks" the list [1100, 720] into two numbers.
        self.minsize(*theme.get("window_min_size", [1100, 720]))

        # Our conversations live in memory for now (saving them to disk is a later milestone)
        # Each one looks like: {"id": 1, "title": "...", "time": "Today, 10:24 AM", "messages": [...]}
        self.conversations = []
        # The conversation we are looking at right now
        self.current_conversation = None
        # Every new conversation gets the next number as its id: 1, 2, 3...
        self.next_conversation_id = 1
        # True while the model is answering. We use it to block a second message until the first is done.
        self.is_generating = False
        # The last model that loaded without problems, so we can go back to it if a new one fails
        self.previous_model_file = None
        # True while a model is loading on its worker thread. We block chatting and switching until it is done.
        self.is_loading = False
        # The mailbox the loading worker thread uses to tell us "loaded" or "error"
        self.load_mailbox = queue.Queue()
        # The mailbox the model's worker thread drops each new piece of the answer into
        self.answer_mailbox = queue.Queue()
        # An on/off flag both threads can see. We switch it on to tell the worker to stop early.
        self.stop_answer = threading.Event()
        # When you close the window, tell the worker to stop first (see on_close below)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Build all the widgets, start the first empty chat, and show the Chat page
        self.build_layout()
        self.new_chat()
        self.show_page("Chat")

        # Draw the window FIRST, then load the model, so you see the app while the model loads
        # The Send button stays off until the model is ready
        self.input_bar.set_busy(True)
        # after(200, ...) waits 200 milliseconds (so the window can appear), then loads the model
        self.after(200, self.load_model)

    # ---------- Building the window ----------
    def build_layout(self):
        # grid() splits the window into a table. Column 0 = sidebar, column 1 = everything else.
        # weight=1 means column 1 / row 0 get all the extra space when the window grows.
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # The sidebar gets three "callbacks": OUR methods that it should call when its buttons are clicked
        self.sidebar = Sidebar(self, on_nav=self.show_page, on_new_chat=self.new_chat,
                               on_select_conversation=self.open_conversation)
        # sticky="ns" ("north-south") stretches the sidebar from the top to the bottom of the window
        self.sidebar.grid(row=0, column=0, sticky="ns", padx=(16, 8), pady=16)

        # The right side of the window. sticky="nsew" stretches it in every direction.
        main_area = ctk.CTkFrame(self, fg_color="transparent")
        main_area.grid(row=0, column=1, sticky="nsew", padx=(8, 16), pady=16)

        # The model header goes across the top of the right side
        self.header = ModelHeader(main_area, list_models=llm.list_models,
                                  on_select_model=self.switch_model, on_add_model=self.open_add_model)
        self.header.pack(fill="x", pady=(0, 12))

        # Each sidebar button shows a "page". The Chat page holds the chat and the input bar.
        # self.pages is a dictionary: page name -> the frame for that page
        self.pages = {}
        chat_page = ctk.CTkFrame(main_area, fg_color="transparent")
        self.chat_view = ChatView(chat_page)
        # expand=True makes the chat take all the space the input bar does not use
        self.chat_view.pack(fill="both", expand=True)
        # We hand the input bar our send_message method, and llm.count_tokens for the token counter
        self.input_bar = InputBar(chat_page, on_send=self.send_message,
                                  count_tokens=llm.count_tokens, context_size=llm.context_size)
        self.input_bar.pack(fill="x", pady=(12, 0))
        self.pages["Chat"] = chat_page

    # Hide every page, then show the one we clicked
    # pack_forget() takes a widget off the screen without deleting it, so we can show it again later
    def show_page(self, page_name):
        for page in self.pages.values():
            page.pack_forget()
        self.pages[page_name].pack(fill="both", expand=True)
        # Tell the sidebar which button to light up
        self.sidebar.set_active_page(page_name)

    # ---------- Loading the model ----------
    # Here is another BIG DEAL. This is where the LLM gets loaded into memory (see llm.py)
    # file_name is which model to load. None means "the starting model".
    # Loading takes several seconds, so the real work happens on a worker thread (load_model_worker)
    # and the window stays free to move, resize and tick the clock while it loads.
    def load_model(self, file_name=None):
        self.is_loading = True
        self.input_bar.set_busy(True)
        self.header.set_status("loading")
        worker = threading.Thread(target=self.load_model_worker, args=(file_name,), daemon=True)
        worker.start()
        self.read_load_mailbox(file_name)

    # ---------- Runs on the WORKER thread ----------
    # Load the model, then leave ONE note in the mailbox saying how it went. No widgets here!
    def load_model_worker(self, file_name):
        try:
            llm.load_model(file_name)
            self.load_mailbox.put(("loaded", None))
        except ValueError as error:
            # The file is broken or is not a model llama.cpp understands
            self.load_mailbox.put(("error", str(error)))
        except SystemExit:
            # llm.load_model() calls exit() when the models folder is empty. exit() inside a thread
            # only ends that thread, so we pass the news to the main thread to close the app.
            self.load_mailbox.put(("no_models", None))

    # ---------- Runs on the MAIN thread ----------
    # Check the mailbox every 100 ms until the worker leaves its note, then update the screen
    def read_load_mailbox(self, file_name):
        try:
            kind, text = self.load_mailbox.get_nowait()
        except queue.Empty:
            # No note yet, the model is still loading. Check again soon.
            self.after(100, self.read_load_mailbox, file_name)
            return
        self.is_loading = False

        if kind == "no_models":
            self.on_close()
            return
        if kind == "error":
            print(f"Could not load {file_name}: {text}")
            self.header.set_status("error")
            self.header.model_name_label.configure(text=file_name or "No model")
            # Go back to the model that worked before, if there was one
            if self.previous_model_file and self.previous_model_file != file_name:
                self.after(1500, self.switch_model, self.previous_model_file)
            return
        self.previous_model_file = llm.model_file
        # Now that the model is loaded, read its real facts and show them in the header
        self.header.set_model_info(llm.model_info())
        self.header.set_status("connected")
        # Turn the Send button on, we are ready to chat
        self.input_bar.set_busy(False)

    # Runs when you pick a model from the dropdown in the header
    def switch_model(self, file_name):
        # Do not swap models while one is still answering, or if it is already loaded
        # Also do not start a second load while one is already running
        # (After a failed load llm.model is None but model_file still has the old name, so we check both.)
        if self.is_generating or self.is_loading or (llm.model is not None and file_name == llm.model_file):
            return
        self.header.model_name_label.configure(text="Loading…")
        # No more waiting first: load_model() hands the work to a thread, so the window never freezes
        self.load_model(file_name)

    # Runs when you pick "Add a model from Hugging Face…" from the dropdown.
    # When a download finishes, its "Use This Model" button calls switch_model.
    def open_add_model(self):
        AddModelDialog(self, on_use=self.switch_model)

    # ---------- Conversations ----------
    # Start a brand new, empty conversation (the + button in the sidebar)
    def new_chat(self):
        # Do not switch conversations while the model is still answering
        if self.is_generating:
            return
        conversation = {"id": self.next_conversation_id, "title": "New Chat",
                        "time": "Today, " + time_now(), "messages": []}
        self.next_conversation_id += 1
        # insert(0, ...) puts the newest conversation at the top of the list
        self.conversations.insert(0, conversation)
        self.open_conversation(conversation["id"])

    # Show a conversation in the chat area (runs when you click one in the sidebar)
    def open_conversation(self, conversation_id):
        if self.is_generating:
            return
        # next(...) finds the FIRST conversation in our list whose id matches
        self.current_conversation = next(c for c in self.conversations if c["id"] == conversation_id)
        # Redraw the chat from the saved messages
        self.chat_view.clear()
        for message in self.current_conversation["messages"]:
            card = self.chat_view.add_message(message["role"], message["text"], message["time"])
            # AI messages also get their "67 tokens | 2.4s | Completed" footer back
            if message["role"] == "ai":
                card.show_completed(message["tokens"], message["seconds"])
        # Redraw the sidebar list so the conversation we opened glows
        self.sidebar.set_conversations(self.conversations, conversation_id)
        self.show_page("Chat")

    # ---------- Sending a message and streaming the answer ----------
    # Now lets create a function to handle user input and response from the LLM
    # input_bar.py calls this with the text you typed
    def send_message(self, user_text):
        # Do nothing if the model is already answering, or is not loaded yet
        if self.is_generating or self.is_loading or llm.model is None:
            return
        self.is_generating = True
        self.input_bar.set_busy(True)
        conversation = self.current_conversation

        # The first message becomes the conversation's title in the sidebar
        # If it is longer than 22 letters, we cut it and add "…" so it fits
        if not conversation["messages"]:
            conversation["title"] = user_text if len(user_text) <= 22 else user_text[:21].rstrip() + "…"
            self.sidebar.set_conversations(self.conversations, conversation["id"])

        # Save your message in the conversation, then show it as an orange card
        conversation["messages"].append({"role": "user", "text": user_text, "time": time_now()})
        self.chat_view.add_message("user", user_text, time_now())

        # Make an empty AI card. The worker thread will fill it one token at a time.
        # We save everything the mailbox reader needs on self, so read_answer_mailbox() can find it
        self.answer_card = self.chat_view.add_message("ai", "", time_now())
        self.answer_conversation = conversation
        self.answer_time = time_now()
        # time.time() is the current time in seconds. We save it to measure how long the answer takes.
        self.answer_start = time.time()
        self.answer_tokens = 0

        # Start the worker thread. We hand it a COPY of the messages (list(...)), so the worker
        # never reads the list while the main thread might be changing it.
        # daemon=True means the thread will not keep the app alive after the window closes.
        self.stop_answer.clear()
        worker = threading.Thread(target=self.generate_answer, args=(list(conversation["messages"]),), daemon=True)
        worker.start()
        # Start checking the mailbox for pieces of the answer (this runs on the main thread)
        self.read_answer_mailbox()

    # ---------- Runs on the WORKER thread ----------
    # BIG DEAL: llm.stream_response() hands us the answer one piece (token) at a time.
    # This can take many seconds, which is why it runs here and not on the main thread.
    # GOLDEN RULE: this method never touches a widget. It only puts notes in the mailbox:
    #   ("piece", "Hello")  -> one new piece of the answer
    #   ("error", "...")    -> something went wrong
    #   ("done", None)      -> the answer is finished
    def generate_answer(self, messages):
        try:
            for piece in llm.stream_response(messages):
                # If the window is closing, stop asking the model for more
                if self.stop_answer.is_set():
                    break
                self.answer_mailbox.put(("piece", piece))
        except Exception as error:
            # Send the error to the main thread so it can show it, instead of the thread dying silently
            self.answer_mailbox.put(("error", str(error)))
        self.answer_mailbox.put(("done", None))

    # ---------- Runs on the MAIN thread ----------
    # Take every note out of the mailbox and update the screen, then check again in 30 milliseconds
    def read_answer_mailbox(self):
        card = self.answer_card
        try:
            # get_nowait() takes one note out, or raises queue.Empty when the mailbox is empty
            while True:
                kind, text = self.answer_mailbox.get_nowait()
                if kind == "piece":
                    self.answer_tokens += 1
                    # Add the new piece to the card and update the "Generating…" footer
                    card.append_text(text)
                    card.show_generating(self.answer_tokens, time.time() - self.answer_start)
                    # Keep the newest part of the answer in view
                    self.chat_view.scroll_to_bottom()
                elif kind == "error":
                    print("The model ran into a problem:", text)
                    card.append_text("\n\n[Error: " + text + "]")
                elif kind == "done":
                    self.finish_answer()
                    # The answer is finished, so we stop checking the mailbox
                    return
        except queue.Empty:
            pass
        # after() runs this again in 30 ms. The window stays free to scroll, resize and tick the clock.
        self.after(30, self.read_answer_mailbox)

    # The answer is done! Show "Completed", save it, and let the user send the next message
    def finish_answer(self):
        seconds = time.time() - self.answer_start
        self.answer_card.show_completed(self.answer_tokens, seconds)
        # Save the AI answer in the conversation so it comes back when you reopen this chat
        self.answer_conversation["messages"].append({"role": "ai", "text": self.answer_card.body.cget("text"),
                                                     "time": self.answer_time, "tokens": self.answer_tokens,
                                                     "seconds": seconds})
        # Ready for the next message
        self.is_generating = False
        self.input_bar.set_busy(False)

    # Runs when you click the window's close button
    def on_close(self):
        # Tell the worker thread to stop, then close the window
        self.stop_answer.set()
        self.destroy()


# App start here
# This "if" is True only when you run "python main.py" directly (not when another file imports main.py)
if __name__ == "__main__":
    # Create our app (this runs __init__ above)
    app = VortexaApp()
    # Must have this to run our app. mainloop() keeps the window open and listens for clicks and key presses.
    app.mainloop()
