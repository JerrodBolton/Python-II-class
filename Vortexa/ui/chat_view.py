# The chat area: a scrollable list of message cards
#   You      -> orange card with a person avatar
#   VORTEXA  -> green card with an orbit avatar, plus token stats and action buttons
#
# Each message is its own MessageCard. ChatView is the scrolling box that holds all the cards.

# We use plain tkinter for one thing: resizing the scrolling frame in clear()
import tkinter as tk
# customtkinter gives us modern widgets (frames, labels, buttons) built on top of tkinter
import customtkinter as ctk
# Our theme colors, corner sizes, font helper and color mixer
from theme import colors, radius, font, blend
# load_icon("user", 22, "#FF731C") gives us a colored icon
from icons import load_icon
# Our shared building blocks from ui/widgets.py
from ui.widgets import GlowCard, Avatar


# One message on the screen: an avatar on the left and a glowing card on the right
class MessageCard(ctk.CTkFrame):
    #   role      = "user" for your messages, "ai" for VORTEXA's answers
    #   text      = the message words (an AI card starts empty "" and fills up while streaming)
    #   time_text = the time to show, like "10:24 AM"
    def __init__(self, master, role, text, time_text):
        # The outer frame is see-through, it only holds the avatar and the card side by side
        super().__init__(master, fg_color="transparent")
        self.role = role
        # True or False, we use it below to pick colors, icons and names
        is_user = role == "user"
        # Orange for you, green for VORTEXA
        accent = colors["primary"] if is_user else colors["secondary"]

        # grid() lets us put the avatar in column 0 and the card in column 1
        # weight=1 tells column 1 to take all the extra width
        self.grid_columnconfigure(1, weight=1)
        avatar_icon = load_icon("user" if is_user else "ai", 22, accent)
        # sticky="n" ("north") keeps the avatar at the TOP of the row, even when the message is long
        Avatar(self, avatar_icon, accent).grid(row=0, column=0, sticky="n", padx=(4, 16), pady=(6, 0))

        # The glowing card that holds the message
        card = GlowCard(self, glow_color=accent, fill_color=colors["user_card"] if is_user else colors["ai_card"],
                        radius=radius["card"], glow_strength=0.3)
        # sticky="ew" ("east-west") stretches the card across the whole width of column 1
        card.grid(row=0, column=1, sticky="ew")
        # A short name for the inside of the card, where all the message widgets go
        inside = card.inner

        # ---------- Name + time ----------
        title_row = ctk.CTkFrame(inside, fg_color="transparent")
        title_row.pack(fill="x", padx=24, pady=(14, 2))
        # "You" in white for your messages, "VORTEXA" in green for the AI
        ctk.CTkLabel(title_row, text="You" if is_user else "VORTEXA", font=font(16, "bold"),
                     text_color=colors["text"] if is_user else colors["secondary"], height=20).pack(side="left")
        ctk.CTkLabel(title_row, text=time_text, font=font(12), text_color=colors["text_muted"],
                     height=20).pack(side="left", padx=(14, 0))

        # ---------- The message text ----------
        # justify="left" lines up wrapped lines on the left, anchor="w" sticks the text to the left side
        # wraplength is how wide a line can get (in pixels) before it wraps to the next line.
        # 600 is just a starting value, ChatView changes it to fit the window (see set_wrap below)
        self.body = ctk.CTkLabel(inside, text=text, font=font(15), text_color=colors["text"],
                                 justify="left", anchor="w", wraplength=600)
        self.body.pack(fill="x", padx=24, pady=(4, 14))

        # ---------- Footer (AI messages only) ----------
        # The footer shows "67 tokens | 2.4s | ✓ Completed" and the copy / thumbs buttons
        if not is_user:
            self.footer = ctk.CTkFrame(inside, fg_color="transparent")
            self.footer.pack(fill="x", padx=24, pady=(0, 12))
            # The token and time numbers
            self.stats_label = ctk.CTkLabel(self.footer, text="", font=font(12), text_color=colors["text_muted"], height=18)
            self.stats_label.pack(side="left")
            # The green check icon (empty while generating)
            self.status_icon = ctk.CTkLabel(self.footer, text="", height=18)
            self.status_icon.pack(side="left", padx=(10, 4))
            # "Generating…" in orange or "Completed" in green
            self.status_label = ctk.CTkLabel(self.footer, text="", font=font(12), height=18)
            self.status_label.pack(side="left")
            # A frame for the copy / thumbs buttons. We create it now, but only SHOW it when the answer is done.
            self.actions = ctk.CTkFrame(self.footer, fg_color="transparent")
            # The thumbs rating: None, "up" or "down"
            self.rating = None

    # ---------- Used while the AI is "typing" ----------
    # Add one new piece of text (one token) to the end of the message
    # cget("text") GETS the current text, then we add the piece and put it back with configure()
    def append_text(self, piece):
        self.body.configure(text=self.body.cget("text") + piece)

    # Change how wide the text can get before it wraps
    # max(width, 200) makes sure it is never smaller than 200 pixels, even in a tiny window
    def set_wrap(self, width):
        self.body.configure(wraplength=max(width, 200))

    # Footer while streaming, for example "42 tokens  •  12.6 tokens/s  •  Generating…"
    def show_generating(self, token_count, seconds):
        # Tokens per second = how many tokens / how many seconds. We check seconds > 0 so we never divide by zero.
        speed = token_count / seconds if seconds > 0 else 0
        # {speed:.1f} shows the number with 1 digit after the decimal point, like 12.6
        self.stats_label.configure(text=f"{token_count} tokens   •   {speed:.1f} tokens/s   •")
        self.status_icon.configure(image=None)
        self.status_label.configure(text="Generating…", text_color=colors["primary"])

    # Footer when the answer is finished, for example "67 tokens | 2.4s | ✓ Completed"
    def show_completed(self, token_count, seconds):
        self.stats_label.configure(text=f"{token_count} tokens    |    {seconds:.1f}s    |")
        self.status_icon.configure(image=load_icon("check", 16, colors["secondary"]))
        self.status_label.configure(text="Completed", text_color=colors["secondary"])
        self._add_action_buttons()

    # Copy, thumbs up and thumbs down buttons on the right side of a finished AI message
    # The _ at the start of the name means "this is only used inside this class"
    def _add_action_buttons(self):
        # winfo_ismapped() is True if the frame is already on the screen. If so, do not add the buttons twice.
        if self.actions.winfo_ismapped():
            return
        self.actions.pack(side="right")
        self.copy_button = self._small_button("copy", self.copy_text)
        # lambda: self.rate("up") is a tiny function that calls rate with "up" when the button is clicked
        self.like_button = self._small_button("thumbs_up", lambda: self.rate("up"))
        self.dislike_button = self._small_button("thumbs_down", lambda: self.rate("down"))

    # Helper that makes one small icon-only button
    def _small_button(self, icon_name, command):
        button = ctk.CTkButton(self.actions, text="", width=30, height=28, fg_color="transparent",
                               # A faint green background when the mouse hovers over the button
                               hover_color=blend(colors["ai_card"], colors["secondary"], 0.15),
                               image=load_icon(icon_name, 18, colors["text_muted"]), command=command)
        button.pack(side="left", padx=2)
        return button

    # Put the AI answer on the clipboard so you can paste it anywhere
    def copy_text(self):
        # Empty the clipboard first, then add our text
        self.clipboard_clear()
        self.clipboard_append(self.body.cget("text"))
        # Show a green check for one second so we know it worked, then put the copy icon back
        # after(1000, ...) means "run this in 1000 milliseconds (1 second)" without freezing the app
        self.copy_button.configure(image=load_icon("check", 18, colors["secondary"]))
        self.after(1000, lambda: self.copy_button.configure(image=load_icon("copy", 18, colors["text_muted"])))

    # Thumbs up / down. Clicking the same one again turns it off.
    # (For now this only changes the color. Saving ratings comes later.)
    def rate(self, choice):
        # If we click the one that is already chosen, set it back to None (off), otherwise choose it
        self.rating = None if self.rating == choice else choice
        # Green thumbs up when chosen, red thumbs down when chosen, gray when not chosen
        self.like_button.configure(image=load_icon("thumbs_up", 18, colors["secondary"] if self.rating == "up" else colors["text_muted"]))
        self.dislike_button.configure(image=load_icon("thumbs_down", 18, colors["error"] if self.rating == "down" else colors["text_muted"]))


# The big rounded box that holds all the message cards and scrolls up and down
class ChatView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=colors["panel"], corner_radius=radius["panel"],
                         border_width=1, border_color=colors["panel_border"])
        # A list of every MessageCard on the screen, so we can re-wrap or delete them later
        self.cards = []

        # CTkScrollableFrame is a frame with a scrollbar built in. The cards go inside it.
        self.messages_frame = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                                     scrollbar_button_color=colors["surface"],
                                                     scrollbar_button_hover_color=colors["surface_hover"])
        self.messages_frame.pack(fill="both", expand=True, padx=8, pady=10)
        # When the window changes size, re-wrap the text in every card
        # "<Configure>" is the event tkinter sends whenever a widget changes size
        # add="+" is IMPORTANT: it ADDS our job instead of replacing the one already there.
        # CTkScrollableFrame uses this same event to measure how tall the messages are.
        # Without "+" it never learns the chat got taller than the window, so you cannot scroll.
        self.messages_frame.bind("<Configure>", lambda event: self._update_wrap(), add="+")

        # Shown when the chat is empty
        # We use place() so the words float in the middle of the chat area
        self.empty_label = ctk.CTkLabel(self, text="Ask VORTEXA anything to begin.", font=font(16),
                                        text_color=colors["text_muted"])
        self.empty_label.place(relx=0.5, rely=0.5, anchor="center")

    # Add one message card and return it, so main.py can stream text into it
    def add_message(self, role, text, time_text):
        # Hide the "Ask VORTEXA anything" words now that we have a message
        self.empty_label.place_forget()
        card = MessageCard(self.messages_frame, role, text, time_text)
        card.pack(fill="x", padx=(10, 14), pady=8)
        # Make the new card's text wrap to the current window width
        card.set_wrap(self._wrap_width())
        self.cards.append(card)
        self.scroll_to_bottom()
        # main.py keeps this card so it can add tokens to it while the AI answers
        return card

    # Remove every card (used for New Chat and switching conversations)
    def clear(self):
        for card in self.cards:
            card.destroy()
        self.cards = []
        # A tkinter quirk: when a frame loses ALL its widgets, it keeps its old size instead of shrinking.
        # So we ask for a tiny height ourselves, and scroll back to the top for the new chat.
        # (As soon as a new card is added, the frame grows to fit it again.)
        tk.Frame.configure(self.messages_frame, height=1)
        self.messages_frame._parent_canvas.yview_moveto(0)
        # Show the "Ask VORTEXA anything" words again
        self.empty_label.place(relx=0.5, rely=0.5, anchor="center")

    def scroll_to_bottom(self):
        # update_idletasks lets tkinter finish drawing first, so it knows how tall everything is
        self.update_idletasks()
        # yview_moveto(1.0) scrolls to 100% of the way down (0.0 would be the top)
        self.messages_frame._parent_canvas.yview_moveto(1.0)

    # How wide the message text can be: the chat width minus the avatar, gaps and padding
    def _wrap_width(self):
        return self.messages_frame.winfo_width() - 150

    # Tell every card the new wrap width (runs every time the window is resized)
    def _update_wrap(self):
        width = self._wrap_width()
        for card in self.cards:
            card.set_wrap(width)
