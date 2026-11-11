# The sidebar on the left: logo, app name, navigation buttons and the conversation list
#
#   +--------------------+
#   |   (orb logo)       |
#   |   VORTEXA          |
#   |   LOCAL LLM ...    |
#   |  [ Chat         ]  |  <- NavItem (glows when active)
#   |  CONVERSATIONS  +  |
#   |  [ Chat title   ]  |  <- ConversationItem
#   +--------------------+

# customtkinter gives us modern widgets (frames, labels, buttons) built on top of tkinter
import customtkinter as ctk
# Our theme: colors, corner sizes, the brand name/tagline and our font helper
from theme import colors, radius, brand, font
# load_icon("chat", 22, "#FF731C") gives us a colored icon
from icons import load_icon
# The round orb logo and the glowing VORTEXA name
from logo import load_logo, load_wordmark
# Our shared building blocks from ui/widgets.py
from ui.widgets import GlowCard, divider

# The pages in our navigation. (name shown on the button, icon file name)
# This is a list of tuples. A tuple is like a list that cannot be changed, written with ( )
# Want a new page? Add a line here, put an icon in assets/icons, and add the page in main.py
nav_pages = [
    ("Chat", "chat"),
]


# Make widgets react to a click right away: when the mouse button goes down, run command().
# lambda event: command() is a tiny function that ignores the click event and just calls command()
# cursor="hand2" shows the pointing-hand mouse cursor so it feels like a button
def make_clickable(widgets, command):
    for widget in widgets:
        widget.bind("<Button-1>", lambda event: command(), add="+")
        widget.configure(cursor="hand2")


# One button in the navigation list. It glows orange when it is the active page.
# NavItem IS a GlowCard (inheritance), with a CTkButton inside it
class NavItem(GlowCard):
    #   text      = the words on the button, like "Chat"
    #   icon_name = the icon file name, like "chat"
    #   command   = the function to run when the button is clicked
    def __init__(self, master, text, icon_name, command):
        # Start with the glow and fill the SAME color as the sidebar, so the card is invisible until active
        super().__init__(master, glow_color=colors["panel"], fill_color=colors["panel"], radius=radius["button"])
        # Remember the icon name so we can recolor the icon later in set_active()
        self.icon_name = icon_name
        # The real clickable button lives inside the card's inner frame
        # "   " + text adds spaces so the words are not squished against the icon
        # anchor="w" ("west") lines the icon and text up on the left side of the button
        # We leave out command= on purpose, see the note below the button
        self.button = ctk.CTkButton(self.inner, text="   " + text, anchor="w", height=42,
                                    font=font(15), fg_color="transparent", corner_radius=radius["button"],
                                    hover_color=colors["surface"], text_color=colors["nav_text"],
                                    image=load_icon(icon_name, 22, colors["nav_icon"]))
        self.button.pack(fill="x", padx=4, pady=3)
        # Why no command= on the button? A CTkButton only runs its command when you LET GO of the mouse,
        # and only if it noticed the mouse arrive first. It also "forgets" the mouse for a moment after
        # every click. So quick clicks, or clicks right after moving the mouse, were often ignored.
        # Instead we run the command the moment the mouse button goes DOWN, like the conversation items do.
        # We also bind the glowing card around the button, so its edges are clickable too.
        make_clickable([self, self.inner, self.button], command)

    # active=True makes the button glow orange, active=False makes it plain again
    def set_active(self, active):
        if active:
            # Orange glow, dark orange fill, white bold text and a white icon
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
    #   title     = the conversation title, like "Explain what a large..."
    #   time_text = when it started, like "Today, 10:24 AM"
    #   active    = True if this is the conversation we are looking at right now
    #   command   = the function to run when it is clicked
    def __init__(self, master, title, time_text, active, command):
        # This is a "conditional expression": value_if_true if condition else value_if_false
        glow = colors["primary"] if active else colors["panel"]
        fill = colors["nav_active"] if active else colors["panel"]
        super().__init__(master, glow_color=glow, fill_color=fill, radius=radius["button"], glow_strength=0.4)
        # Hide the soft outer glow on items that are not active
        if not active:
            self.configure(border_color=colors["panel"])

        # The little chat bubble icon on the left. White when active, gray when not.
        icon = ctk.CTkLabel(self.inner, text="", image=load_icon("conversation", 18, colors["text"] if active else colors["nav_icon"]))
        icon.pack(side="left", padx=(12, 10), pady=10)
        # A see-through frame to stack the title on top of the time
        text_box = ctk.CTkFrame(self.inner, fg_color="transparent")
        text_box.pack(side="left", fill="x", expand=True, pady=6)
        title_label = ctk.CTkLabel(text_box, text=title, font=font(13), anchor="w", text_color=colors["text"], height=18)
        title_label.pack(fill="x")
        time_label = ctk.CTkLabel(text_box, text=time_text, font=font(11), anchor="w", text_color=colors["text_muted"], height=16)
        time_label.pack(fill="x")

        # Make every part of the item clickable, not just the empty space
        make_clickable([self, self.inner, icon, text_box, title_label, time_label], command)


class Sidebar(ctk.CTkFrame):
    # on_nav(page_name), on_new_chat(), on_select_conversation(conversation_id) are functions from main.py
    # This is called a "callback": the sidebar does not know what the buttons DO, it just calls main.py
    def __init__(self, master, on_nav, on_new_chat, on_select_conversation):
        # width=290 keeps the sidebar the same width no matter how big the window is
        super().__init__(master, fg_color="transparent", width=290)
        # Save this callback with self. so set_conversations() can use it later
        self.on_select_conversation = on_select_conversation

        # The big orange-glowing panel that holds everything in the sidebar
        card = GlowCard(self, glow_color=colors["primary"], fill_color=colors["panel"], radius=radius["panel"], glow_strength=0.4)
        card.pack(fill="both", expand=True)
        # panel is a short name for the inside of the card, where all our widgets go
        panel = card.inner

        # ---------- Logo + name ----------
        # A label with text="" and an image is how CustomTkinter shows a picture
        ctk.CTkLabel(panel, text="", image=load_logo(118)).pack(pady=(22, 6))
        ctk.CTkLabel(panel, text="", image=load_wordmark(30)).pack()
        # Spread the letters apart to get that wide "L O C A L" look
        # " ".join(word) puts a space between every letter: "LOCAL" -> "L O C A L"
        # "   ".join(...) then puts 3 spaces between the words
        spaced_tagline = "   ".join(" ".join(word) for word in brand.get("tagline", "").split())
        ctk.CTkLabel(panel, text=spaced_tagline, font=font(10), text_color=colors["text_muted"]).pack(pady=(2, 14))

        # ---------- Navigation buttons ----------
        # A dictionary so we can find each button by its page name later: self.nav_items["Chat"]
        self.nav_items = {}
        for page_name, icon_name in nav_pages:
            # IMPORTANT: lambda name=page_name: ... "freezes" the page name for THIS button.
            # Without name=page_name every button would remember the LAST page name ("Settings").
            item = NavItem(panel, page_name, icon_name, command=lambda name=page_name: on_nav(name))
            item.pack(fill="x", padx=12, pady=1)
            self.nav_items[page_name] = item

        # A thin line between the navigation and the conversation list
        divider(panel).pack(fill="x", padx=18, pady=(14, 10))

        # ---------- Conversations ----------
        # A row with the "CONVERSATIONS" title on the left and a + button on the right
        conversations_header = ctk.CTkFrame(panel, fg_color="transparent")
        conversations_header.pack(fill="x", padx=18)
        ctk.CTkLabel(conversations_header, text="C O N V E R S A T I O N S", font=font(11),
                     text_color=colors["text_muted"]).pack(side="left")
        # The + button starts a new chat. command=on_new_chat calls main.py's new_chat()
        # 34 x 34 pixels so it is an easy target to hit. Like the nav buttons, it reacts on mouse down.
        plus_button = ctk.CTkButton(conversations_header, text="", width=34, height=34, fg_color="transparent",
                                    hover_color=colors["surface"], image=load_icon("plus", 18, colors["text_muted"]))
        plus_button.pack(side="right")
        make_clickable([plus_button], on_new_chat)

        # A scrollable frame, so a long list of conversations can scroll instead of running off the screen
        # The scrollbar is the same color as the panel, so it stays hidden until you hover over it
        self.conversation_list = ctk.CTkScrollableFrame(panel, fg_color="transparent",
                                                        scrollbar_button_color=colors["panel"],
                                                        scrollbar_button_hover_color=colors["surface"])
        self.conversation_list.pack(fill="both", expand=True, padx=(6, 0), pady=(6, 14))

    # Highlight the page we are on
    # name == page_name is True for only ONE button, so only that button glows
    def set_active_page(self, page_name):
        for name, item in self.nav_items.items():
            item.set_active(name == page_name)

    # Rebuild the list of conversations. conversations is a list of dicts: {"id", "title", "time"}
    # The easiest way to update a list on screen is: delete every old item, then draw the new ones
    def set_conversations(self, conversations, active_id):
        # winfo_children() gives us every widget inside the list. destroy() removes it from the screen.
        for old_item in self.conversation_list.winfo_children():
            old_item.destroy()
        for conversation in conversations:
            # cid=conversation["id"] freezes this conversation's id for this item (same trick as the nav buttons)
            ConversationItem(self.conversation_list, conversation["title"], conversation["time"],
                             active=conversation["id"] == active_id,
                             command=lambda cid=conversation["id"]: self.on_select_conversation(cid)
                             ).pack(fill="x", padx=4, pady=2)
