# Small reusable building blocks that the other ui files share
import customtkinter as ctk
from theme import colors, blend


# GlowCard: a rounded box with a "glowing" border.
# CustomTkinter cannot draw real blurry glow, so we fake it with TWO frames:
#   - an outer frame with a thick, dim border (the soft glow)
#   - an inner frame with a thin, bright border (the sharp edge)
# Put your widgets inside card.inner, not inside the card itself.
class GlowCard(ctk.CTkFrame):
    def __init__(self, master, glow_color, fill_color, radius=14, glow_strength=0.35, **kwargs):
        soft_glow = blend(colors["background"], glow_color, glow_strength)
        super().__init__(master, fg_color="transparent", corner_radius=radius + 3,
                         border_width=3, border_color=soft_glow, **kwargs)
        self.inner = ctk.CTkFrame(self, fg_color=fill_color, corner_radius=radius,
                                  border_width=1, border_color=glow_color)
        self.inner.pack(fill="both", expand=True, padx=2, pady=2)

    # Change the glow color later, for example when a button becomes active
    def set_glow(self, glow_color, glow_strength=0.35):
        self.configure(border_color=blend(colors["background"], glow_color, glow_strength))
        self.inner.configure(border_color=glow_color)


# A round "avatar" circle with an icon in the middle, used next to chat messages
class Avatar(ctk.CTkFrame):
    def __init__(self, master, icon, ring_color, size=46):
        super().__init__(master, width=size, height=size, corner_radius=size // 2,
                         fg_color=blend(colors["background"], ring_color, 0.12),
                         border_width=2, border_color=ring_color)
        # place() puts the icon exactly in the center
        ctk.CTkLabel(self, text="", image=icon, fg_color="transparent").place(relx=0.5, rely=0.5, anchor="center")


# A thin horizontal line to separate sections
def divider(master, color=None):
    return ctk.CTkFrame(master, height=1, corner_radius=0, fg_color=color or colors["panel_border"])
