# The chat area: a scrollable list of message cards
#   You      -> orange card with a person avatar
#   VORTEXA  -> green card with an orbit avatar, plus token stats and action buttons
import customtkinter as ctk
from theme import colors, radius, font, blend
from icons import load_icon
from ui.widgets import GlowCard, Avatar


class MessageCard(ctk.CTkFrame):
    def __init__(self, master, role, text, time_text):
        super().__init__(master, fg_color="transparent")
        self.role = role
        is_user = role == "user"
        accent = colors["primary"] if is_user else colors["secondary"]

        # grid() lets us put the avatar in column 0 and the card in column 1
        # weight=1 tells column 1 to take all the extra width
        self.grid_columnconfigure(1, weight=1)
        avatar_icon = load_icon("user" if is_user else "ai", 22, accent)
        Avatar(self, avatar_icon, accent).grid(row=0, column=0, sticky="n", padx=(4, 16), pady=(6, 0))

        card = GlowCard(self, glow_color=accent, fill_color=colors["user_card"] if is_user else colors["ai_card"],
                        radius=radius["card"], glow_strength=0.3)
        card.grid(row=0, column=1, sticky="ew")
        inside = card.inner

        # ---------- Name + time ----------
        title_row = ctk.CTkFrame(inside, fg_color="transparent")
        title_row.pack(fill="x", padx=24, pady=(14, 2))
        ctk.CTkLabel(title_row, text="You" if is_user else "VORTEXA", font=font(16, "bold"),
                     text_color=colors["text"] if is_user else colors["secondary"], height=20).pack(side="left")
        ctk.CTkLabel(title_row, text=time_text, font=font(12), text_color=colors["text_muted"],
                     height=20).pack(side="left", padx=(14, 0))

        # ---------- The message text ----------
        # justify="left" lines up wrapped lines on the left, anchor="w" sticks the text to the left side
        self.body = ctk.CTkLabel(inside, text=text, font=font(15), text_color=colors["text"],
                                 justify="left", anchor="w", wraplength=600)
        self.body.pack(fill="x", padx=24, pady=(4, 14))

        # ---------- Footer (AI messages only) ----------
        if not is_user:
            self.footer = ctk.CTkFrame(inside, fg_color="transparent")
            self.footer.pack(fill="x", padx=24, pady=(0, 12))
            self.stats_label = ctk.CTkLabel(self.footer, text="", font=font(12), text_color=colors["text_muted"], height=18)
            self.stats_label.pack(side="left")
            self.status_icon = ctk.CTkLabel(self.footer, text="", height=18)
            self.status_icon.pack(side="left", padx=(10, 4))
            self.status_label = ctk.CTkLabel(self.footer, text="", font=font(12), height=18)
            self.status_label.pack(side="left")
            self.actions = ctk.CTkFrame(self.footer, fg_color="transparent")
            self.rating = None

    # ---------- Used while the AI is "typing" ----------
    def append_text(self, piece):
        self.body.configure(text=self.body.cget("text") + piece)

    def set_wrap(self, width):
        self.body.configure(wraplength=max(width, 200))

    def show_generating(self, token_count, seconds):
        speed = token_count / seconds if seconds > 0 else 0
        self.stats_label.configure(text=f"{token_count} tokens   •   {speed:.1f} tokens/s   •")
        self.status_icon.configure(image=None)
        self.status_label.configure(text="Generating…", text_color=colors["primary"])

    def show_completed(self, token_count, seconds):
        self.stats_label.configure(text=f"{token_count} tokens    |    {seconds:.1f}s    |")
        self.status_icon.configure(image=load_icon("check", 16, colors["secondary"]))
        self.status_label.configure(text="Completed", text_color=colors["secondary"])
        self._add_action_buttons()

    # Copy, thumbs up and thumbs down buttons on the right side of a finished AI message
    def _add_action_buttons(self):
        if self.actions.winfo_ismapped():
            return
        self.actions.pack(side="right")
        self.copy_button = self._small_button("copy", self.copy_text)
        self.like_button = self._small_button("thumbs_up", lambda: self.rate("up"))
        self.dislike_button = self._small_button("thumbs_down", lambda: self.rate("down"))

    def _small_button(self, icon_name, command):
        button = ctk.CTkButton(self.actions, text="", width=30, height=28, fg_color="transparent",
                               hover_color=blend(colors["ai_card"], colors["secondary"], 0.15),
                               image=load_icon(icon_name, 18, colors["text_muted"]), command=command)
        button.pack(side="left", padx=2)
        return button

    # Put the AI answer on the clipboard so you can paste it anywhere
    def copy_text(self):
        self.clipboard_clear()
        self.clipboard_append(self.body.cget("text"))
        # Show a green check for one second so we know it worked, then put the copy icon back
        self.copy_button.configure(image=load_icon("check", 18, colors["secondary"]))
        self.after(1000, lambda: self.copy_button.configure(image=load_icon("copy", 18, colors["text_muted"])))

    # Thumbs up / down. Clicking the same one again turns it off.
    # (For now this only changes the color. Saving ratings comes later.)
    def rate(self, choice):
        self.rating = None if self.rating == choice else choice
        self.like_button.configure(image=load_icon("thumbs_up", 18, colors["secondary"] if self.rating == "up" else colors["text_muted"]))
        self.dislike_button.configure(image=load_icon("thumbs_down", 18, colors["error"] if self.rating == "down" else colors["text_muted"]))


class ChatView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=colors["panel"], corner_radius=radius["panel"],
                         border_width=1, border_color=colors["panel_border"])
        self.cards = []

        self.messages_frame = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                                     scrollbar_button_color=colors["surface"],
                                                     scrollbar_button_hover_color=colors["surface_hover"])
        self.messages_frame.pack(fill="both", expand=True, padx=8, pady=10)
        # When the window changes size, re-wrap the text in every card
        self.messages_frame.bind("<Configure>", lambda event: self._update_wrap())

        # Shown when the chat is empty
        self.empty_label = ctk.CTkLabel(self, text="Ask VORTEXA anything to begin.", font=font(16),
                                        text_color=colors["text_muted"])
        self.empty_label.place(relx=0.5, rely=0.5, anchor="center")

    # Add one message card and return it, so main.py can stream text into it
    def add_message(self, role, text, time_text):
        self.empty_label.place_forget()
        card = MessageCard(self.messages_frame, role, text, time_text)
        card.pack(fill="x", padx=(10, 14), pady=8)
        card.set_wrap(self._wrap_width())
        self.cards.append(card)
        self.scroll_to_bottom()
        return card

    # Remove every card (used for New Chat and switching conversations)
    def clear(self):
        for card in self.cards:
            card.destroy()
        self.cards = []
        self.empty_label.place(relx=0.5, rely=0.5, anchor="center")

    def scroll_to_bottom(self):
        # update_idletasks lets tkinter finish drawing first, so it knows how tall everything is
        self.update_idletasks()
        self.messages_frame._parent_canvas.yview_moveto(1.0)

    # How wide the message text can be: the chat width minus the avatar, gaps and padding
    def _wrap_width(self):
        return self.messages_frame.winfo_width() - 150

    def _update_wrap(self):
        width = self._wrap_width()
        for card in self.cards:
            card.set_wrap(width)
