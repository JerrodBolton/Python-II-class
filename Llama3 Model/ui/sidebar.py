# The sidebar on the left: logo, app name, navigation buttons and the conversation list
import customtkinter as ctk
from theme import colors, radius, brand, font
from icons import load_icon
from logo import load_logo, load_wordmark
from ui.widgets import GlowCard, divider

# The pages in our navigation. (name shown on the button, icon file name)
nav_pages = [
    ("Chat", "chat"),
    ("Models", "models"),
    ("Knowledge Base", "knowledge"),
    ("Prompts", "prompts"),
    ("RAG & Documents", "documents"),
    ("Settings", "settings"),
]


# One button in the navigation list. It glows orange when it is the active page.
class NavItem(GlowCard):
    def __init__(self, master, text, icon_name, command):
        super().__init__(master, glow_color=colors["panel"], fill_color=colors["panel"], radius=radius["button"])
        self.icon_name = icon_name
        self.button = ctk.CTkButton(self.inner, text="   " + text, anchor="w", height=42, command=command,
                                    font=font(15), fg_color="transparent", corner_radius=radius["button"],
                                    hover_color=colors["surface"], text_color=colors["nav_text"],
                                    image=load_icon(icon_name, 22, colors["nav_icon"]))
        self.button.pack(fill="x", padx=4, pady=3)

    def set_active(self, active):
        if active:
            self.set_glow(colors["primary"], 0.45)
            self.inner.configure(fg_color=colors["nav_active"])
            self.button.configure(text_color=colors["text"], font=font(15, "bold"),
                                  hover_color=colors["nav_active"], image=load_icon(self.icon_name, 22, colors["text"]))
        else:
            # "Turn off" the glow by making the borders the same color as the sidebar
            self.configure(border_color=colors["panel"])
            self.inner.configure(fg_color=colors["panel"], border_color=colors["panel"])
            self.button.configure(text_color=colors["nav_text"], font=font(15),
                                  hover_color=colors["surface"], image=load_icon(self.icon_name, 22, colors["nav_icon"]))


# One conversation in the list (title + time). Clicking it opens that conversation.
class ConversationItem(GlowCard):
    def __init__(self, master, title, time_text, active, command):
        glow = colors["primary"] if active else colors["panel"]
        fill = colors["nav_active"] if active else colors["panel"]
        super().__init__(master, glow_color=glow, fill_color=fill, radius=radius["button"], glow_strength=0.4)
        if not active:
            self.configure(border_color=colors["panel"])

        icon = ctk.CTkLabel(self.inner, text="", image=load_icon("conversation", 18, colors["text"] if active else colors["nav_icon"]))
        icon.pack(side="left", padx=(12, 10), pady=10)
        text_box = ctk.CTkFrame(self.inner, fg_color="transparent")
        text_box.pack(side="left", fill="x", expand=True, pady=6)
        title_label = ctk.CTkLabel(text_box, text=title, font=font(13), anchor="w", text_color=colors["text"], height=18)
        title_label.pack(fill="x")
        time_label = ctk.CTkLabel(text_box, text=time_text, font=font(11), anchor="w", text_color=colors["text_muted"], height=16)
        time_label.pack(fill="x")

        # Make every part of the item clickable, not just the empty space
        for widget in (self.inner, icon, text_box, title_label, time_label):
            widget.bind("<Button-1>", lambda event: command())
            widget.configure(cursor="hand2")


class Sidebar(ctk.CTkFrame):
    # on_nav(page_name), on_new_chat(), on_select_conversation(conversation_id) are functions from main.py
    # This is called a "callback": the sidebar does not know what the buttons DO, it just calls main.py
    def __init__(self, master, on_nav, on_new_chat, on_select_conversation):
        super().__init__(master, fg_color="transparent", width=290)
        self.on_select_conversation = on_select_conversation

        card = GlowCard(self, glow_color=colors["primary"], fill_color=colors["panel"], radius=radius["panel"], glow_strength=0.4)
        card.pack(fill="both", expand=True)
        panel = card.inner

        # ---------- Logo + name ----------
        ctk.CTkLabel(panel, text="", image=load_logo(118)).pack(pady=(22, 6))
        ctk.CTkLabel(panel, text="", image=load_wordmark(30)).pack()
        # Spread the letters apart to get that wide "L O C A L" look
        spaced_tagline = "   ".join(" ".join(word) for word in brand.get("tagline", "").split())
        ctk.CTkLabel(panel, text=spaced_tagline, font=font(10), text_color=colors["text_muted"]).pack(pady=(2, 14))

        # ---------- Navigation buttons ----------
        self.nav_items = {}
        for page_name, icon_name in nav_pages:
            item = NavItem(panel, page_name, icon_name, command=lambda name=page_name: on_nav(name))
            item.pack(fill="x", padx=12, pady=1)
            self.nav_items[page_name] = item

        divider(panel).pack(fill="x", padx=18, pady=(14, 10))

        # ---------- Conversations ----------
        conversations_header = ctk.CTkFrame(panel, fg_color="transparent")
        conversations_header.pack(fill="x", padx=18)
        ctk.CTkLabel(conversations_header, text="C O N V E R S A T I O N S", font=font(11),
                     text_color=colors["text_muted"]).pack(side="left")
        ctk.CTkButton(conversations_header, text="", width=28, height=28, fg_color="transparent",
                      hover_color=colors["surface"], image=load_icon("plus", 18, colors["text_muted"]),
                      command=on_new_chat).pack(side="right")

        self.conversation_list = ctk.CTkScrollableFrame(panel, fg_color="transparent",
                                                        scrollbar_button_color=colors["panel"],
                                                        scrollbar_button_hover_color=colors["surface"])
        self.conversation_list.pack(fill="both", expand=True, padx=(6, 0), pady=(6, 14))

    # Highlight the page we are on
    def set_active_page(self, page_name):
        for name, item in self.nav_items.items():
            item.set_active(name == page_name)

    # Rebuild the list of conversations. conversations is a list of dicts: {"id", "title", "time"}
    def set_conversations(self, conversations, active_id):
        for old_item in self.conversation_list.winfo_children():
            old_item.destroy()
        for conversation in conversations:
            ConversationItem(self.conversation_list, conversation["title"], conversation["time"],
                             active=conversation["id"] == active_id,
                             command=lambda cid=conversation["id"]: self.on_select_conversation(cid)
                             ).pack(fill="x", padx=4, pady=2)
