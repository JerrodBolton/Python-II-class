# Small reusable building blocks that the other ui files share
# Think of this file as our "Lego box": GlowCard, Avatar and divider get used all over the app,
# so we build them ONE time here instead of copying the same code into every file.

# customtkinter gives us modern widgets (frames, labels, buttons) built on top of tkinter
import customtkinter as ctk
# colors is our dictionary of theme colors, blend mixes two colors together (see theme.py)
from theme import colors, blend


# GlowCard: a rounded box with a "glowing" border.
# CustomTkinter cannot draw real blurry glow, so we fake it with TWO frames:
#   - an outer frame with a thick, dim border (the soft glow)
#   - an inner frame with a thin, bright border (the sharp edge)
# Put your widgets inside card.inner, not inside the card itself.
#
# "class GlowCard(ctk.CTkFrame)" means GlowCard IS a CTkFrame with extra features added.
# This is called inheritance: we get everything a CTkFrame can do for free.
class GlowCard(ctk.CTkFrame):
    # __init__ runs once, when we create a new GlowCard
    #   master        = the widget this card lives inside (its "parent")
    #   glow_color    = the bright border color, for example orange
    #   fill_color    = the background color inside the card
    #   radius        = how round the corners are
    #   glow_strength = how strong the soft outer glow is (0 = none, 1 = full color)
    #   **kwargs      = "any other settings", passed straight through to CTkFrame
    def __init__(self, master, glow_color, fill_color, radius=14, glow_strength=0.35, **kwargs):
        # Mix the background color with the glow color to get a dim version of the glow
        soft_glow = blend(colors["background"], glow_color, glow_strength)
        # super().__init__ builds the OUTER frame (the CTkFrame part of our class)
        # fg_color="transparent" means the outer frame has no fill, only its thick dim border
        # The outer corners are 3 pixels rounder so they line up with the inner frame
        super().__init__(master, fg_color="transparent", corner_radius=radius + 3,
                         border_width=3, border_color=soft_glow, **kwargs)
        # The INNER frame sits inside the outer one. It has the real fill color and a thin bright border.
        # We save it as self.inner so other files can put their widgets inside it.
        self.inner = ctk.CTkFrame(self, fg_color=fill_color, corner_radius=radius,
                                  border_width=1, border_color=glow_color)
        # fill="both" + expand=True makes the inner frame fill the outer frame
        # padx/pady=2 leaves a 2 pixel gap so the outer glow border still shows around it
        self.inner.pack(fill="both", expand=True, padx=2, pady=2)

    # Change the glow color later, for example when a button becomes active
    def set_glow(self, glow_color, glow_strength=0.35):
        # .configure() changes a setting on a widget that already exists
        self.configure(border_color=blend(colors["background"], glow_color, glow_strength))
        self.inner.configure(border_color=glow_color)


# A round "avatar" circle with an icon in the middle, used next to chat messages
# A circle is just a square frame whose corner radius is half its size
class Avatar(ctk.CTkFrame):
    def __init__(self, master, icon, ring_color, size=46):
        super().__init__(master, width=size, height=size, corner_radius=size // 2,
                         # Fill the circle with a very faint (12%) version of the ring color
                         fg_color=blend(colors["background"], ring_color, 0.12),
                         border_width=2, border_color=ring_color)
        # place() puts the icon exactly in the center
        # relx=0.5, rely=0.5 means "halfway across, halfway down", anchor="center" centers the icon on that spot
        ctk.CTkLabel(self, text="", image=icon, fg_color="transparent").place(relx=0.5, rely=0.5, anchor="center")


# A thin horizontal line to separate sections
# It is just a frame that is 1 pixel tall. We return it so the caller can pack it wherever they want.
# "color or colors[...]" means: use the color we were given, or the panel border color if we got None
def divider(master, color=None):
    return ctk.CTkFrame(master, height=1, corner_radius=0, fg_color=color or colors["panel_border"])
