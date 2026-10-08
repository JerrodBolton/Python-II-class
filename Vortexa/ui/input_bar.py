# The message input area at the bottom:
#   [ Type your message here...                                         ]
#   [📎] [Default ▾] [Web Search ○] [RAG ○]          0 / 1,024 tokens  [ Send ]
import customtkinter as ctk
from theme import colors, radius, font, blend
from icons import load_icon
from ui.widgets import GlowCard

placeholder_text = "Type your message here...  (Shift+Enter for new line)"


class InputBar(GlowCard):
    # on_send(text) is a function from main.py. count_tokens(text) returns how many tokens text uses.
    def __init__(self, master, on_send, count_tokens, context_size):
        super().__init__(master, glow_color=colors["primary"], fill_color=colors["panel"],
                         radius=radius["panel"] - 4, glow_strength=0.45)
        self.on_send = on_send
        self.count_tokens = count_tokens
        self.context_size = context_size
        self._count_job = None
        panel = self.inner

        # ---------- The text box ----------
        self.textbox = ctk.CTkTextbox(panel, height=64, fg_color=colors["panel"], text_color=colors["text"],
                                      font=font(15), wrap="word", border_width=0)
        # Make the blinking typing cursor orange and thicker so we can see where we are typing
        self.textbox._textbox.configure(insertbackground=colors["primary"], insertwidth=3)
        self.textbox.pack(fill="x", padx=14, pady=(10, 0))

        # CTkTextbox has no built-in placeholder, so we lay a gray label on top of it
        # and hide the label as soon as there is text in the box
        self.placeholder = ctk.CTkLabel(panel, text=placeholder_text, font=font(15),
                                        text_color=colors["text_muted"], fg_color=colors["panel"])
        self.placeholder.place(x=24, y=16)
        self.placeholder.bind("<Button-1>", lambda event: self.textbox.focus_set())

        # Pressing Enter sends the message, Shift+Enter makes a new line
        self.textbox.bind("<Return>", self._enter_key_pressed)
        # Every time a key is released, update the placeholder and the token counter
        self.textbox.bind("<KeyRelease>", lambda event: self._text_changed())

        # ---------- The bottom row of controls ----------
        controls = ctk.CTkFrame(panel, fg_color="transparent")
        controls.pack(fill="x", padx=12, pady=(4, 12))

        # Attach button (attaching files comes with RAG in a later milestone, so it is disabled for now)
        ctk.CTkButton(controls, text="", width=34, height=34, fg_color="transparent", state="disabled",
                      image=load_icon("attach", 20, colors["nav_icon"])).pack(side="left", padx=(0, 8))

        # Preset dropdown. Only "Default" exists today, which is your current sampling settings.
        preset_box = GlowCard(controls, glow_color=colors["primary"], fill_color=blend(colors["panel"], colors["primary"], 0.08),
                              radius=10, glow_strength=0.3)
        preset_box.pack(side="left")
        ctk.CTkLabel(preset_box.inner, text="", image=load_icon("sliders", 18, colors["primary"])).pack(side="left", padx=(12, 0))
        self.preset_menu = ctk.CTkOptionMenu(preset_box.inner, values=["Default"], width=120, height=30, font=font(14),
                                             fg_color=preset_box.inner.cget("fg_color"), button_color=preset_box.inner.cget("fg_color"),
                                             button_hover_color=colors["nav_active"], text_color=colors["primary"],
                                             dropdown_fg_color=colors["card"], dropdown_text_color=colors["text"],
                                             dropdown_hover_color=colors["surface"])
        self.preset_menu.pack(side="left", padx=(2, 6), pady=3)

        # Web Search and RAG switches. They are visible now but turned off until we build those features.
        self.web_search_switch = self._toggle_box(controls, "globe", "Web Search")
        self.rag_switch = self._toggle_box(controls, "knowledge", "RAG")

        # Send button
        self.send_button = ctk.CTkButton(controls, text="Send", width=130, height=44, font=font(16, "bold"),
                                         corner_radius=radius["button"], fg_color=colors["primary"],
                                         hover_color=colors["primary_hover"], text_color=colors["text_on_primary"],
                                         image=load_icon("send", 20, colors["text_on_primary"]), compound="left",
                                         command=self.send)
        self.send_button.pack(side="right")

        # Token counter, for example "12 / 1,024 tokens"
        self.token_label = ctk.CTkLabel(controls, text="", font=font(14), text_color=colors["text_muted"])
        self.token_label.pack(side="right", padx=18)
        self._update_token_label(0)

        self.textbox.focus_set()

    # A box with an icon, a label and an on/off switch
    def _toggle_box(self, master, icon_name, text):
        box = ctk.CTkFrame(master, fg_color=colors["card"], corner_radius=10, border_width=1, border_color=colors["card_border"])
        box.pack(side="left", padx=(12, 0))
        ctk.CTkLabel(box, text="", image=load_icon(icon_name, 18, colors["text_muted"])).pack(side="left", padx=(12, 8))
        ctk.CTkLabel(box, text=text, font=font(14), text_color=colors["text_muted"]).pack(side="left")
        switch = ctk.CTkSwitch(box, text="", width=46, state="disabled", progress_color=colors["secondary"],
                               button_color=colors["text_muted"], fg_color=colors["surface"])
        switch.pack(side="left", padx=(12, 4), pady=8)
        return switch

    # ---------- Sending ----------
    def get_text(self):
        # "1.0" means line 1, character 0. "end-1c" means the end, minus the extra newline tkinter adds.
        return self.textbox.get("1.0", "end-1c").strip()

    def send(self):
        text = self.get_text()
        if not text or self.send_button.cget("state") == "disabled":
            return
        # Clear the input box after getting the text for a better user experience
        self.textbox.delete("1.0", "end")
        self._text_changed()
        self.on_send(text)

    def _enter_key_pressed(self, event):
        # Shift+Enter still makes a new line, so the user can type more than one line
        if event.state & 0x1:
            return
        self.send()
        # Return "break" so the Enter key does not also add a new line to the input box
        return "break"

    # Turn the Send button off while the model is thinking, and back on when it is done
    def set_busy(self, busy):
        self.send_button.configure(state="disabled" if busy else "normal",
                                   fg_color=colors["surface"] if busy else colors["primary"])

    # ---------- Placeholder + token counter ----------
    def _text_changed(self):
        has_text = self.textbox.get("1.0", "end-1c") != ""
        if has_text:
            self.placeholder.place_forget()
        else:
            self.placeholder.place(x=24, y=16)
        # Wait until the user stops typing for 250 ms before counting, so we do not count on every key
        if self._count_job:
            self.after_cancel(self._count_job)
        self._count_job = self.after(250, lambda: self._update_token_label(self.count_tokens(self.get_text())))

    def _update_token_label(self, used):
        self.token_label.configure(text=f"{used:,} / {self.context_size:,} tokens")
