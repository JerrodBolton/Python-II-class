# This file loads our icons from assets/icons
# The icons are white line drawings (from the free Lucide icon set).
# Because they are white, we can "paint" them any color we want, so ONE file
# gives us an orange icon, a green icon, a gray icon, and so on.
import os
import customtkinter as ctk
from PIL import Image
from theme import icons_folder

# We remember icons we already made so we do not build the same image twice
_icon_cache = {}


# Example: load_icon("chat", 22, "#FF731C") gives us an orange chat icon 22 pixels big
def load_icon(name, size=20, color="#FFFFFF"):
    key = (name, size, color)
    if key in _icon_cache:
        return _icon_cache[key]

    white_icon = Image.open(os.path.join(icons_folder, name + ".png")).convert("RGBA")
    # Turn "#FF731C" into the numbers (255, 115, 28)
    red, green, blue = (int(color[i:i + 2], 16) for i in (1, 3, 5))
    # Make a solid block of our color, then use the icon's see-through shape (its alpha channel)
    # as a stencil, so only the lines of the icon show our color
    painted_icon = Image.new("RGBA", white_icon.size, (red, green, blue, 255))
    painted_icon.putalpha(white_icon.getchannel("A"))

    # CTkImage shows the picture at the size we ask for and stays sharp on Retina screens
    icon = ctk.CTkImage(light_image=painted_icon, dark_image=painted_icon, size=(size, size))
    _icon_cache[key] = icon
    return icon
