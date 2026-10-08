# This file loads our "Cosmic Gateway" theme from assets/theme.json
# Every other file imports from here, so the colors and fonts live in ONE place.
# Want to change a color? Change it in theme.json, not in the code.
import os
import json

# Build our folder paths from where this file lives, so the app works no matter where we start it from
app_folder = os.path.dirname(os.path.abspath(__file__))
assets_folder = os.path.join(app_folder, "assets")
images_folder = os.path.join(assets_folder, "images")
icons_folder = os.path.join(assets_folder, "icons")
fonts_folder = os.path.join(assets_folder, "fonts")

# Read the JSON file into a Python dictionary
with open(os.path.join(assets_folder, "theme.json")) as theme_file:
    theme = json.load(theme_file)

# Shortcuts so other files can write colors["primary"] instead of theme["colors"]["primary"]
colors = theme.get("colors", {})
radius = theme.get("radius", {"panel": 22, "card": 14, "button": 12})
brand = theme.get("brand", {"name_white": "VORT", "name_orange": "EXA", "tagline": "LOCAL LLM INTERFACE"})
font_family = theme.get("font", {}).get("family", "Helvetica Neue")
font_size = theme.get("font", {}).get("size", 14)


# A small helper to make fonts: font(14) or font(14, "bold")
def font(size=None, weight="normal"):
    return (font_family, size or font_size, weight)


# Blend two hex colors together. amount=0 gives color_a, amount=1 gives color_b.
# We use this to make a "soft" version of a color for our fake glow borders,
# because CustomTkinter cannot draw real glowing shadows.
def blend(color_a, color_b, amount):
    a = [int(color_a[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(color_b[i:i + 2], 16) for i in (1, 3, 5)]
    mixed = [round(a[i] + (b[i] - a[i]) * amount) for i in range(3)]
    return "#{:02X}{:02X}{:02X}".format(*mixed)
