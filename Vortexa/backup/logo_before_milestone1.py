# This file holds everything to do with our app logo
# To be able to build the path to our logo file
import os
# customtkinter shows our logo in the app
import customtkinter as ctk
# Pillow lets us open, crop and resize our logo image so customtkinter can show it
from PIL import Image, ImageDraw

# The path to our logo, we build it from where this file lives so it works no matter where we start the app from
logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "images", "logo.png")

# Create a round logo from assets/images/logo.png
# size is how big the logo will be on the screen, for example load_logo(56)
def load_logo(size):
    logo = Image.open(logo_path).convert("RGBA")
    width, height = logo.size
    # Our logo is a big space picture, so we crop it to just the glowing orb and its rings
    # These numbers are percentages of the picture, so they still work if the logo is resized
    logo = logo.crop((int(width * 0.225), int(height * 0.07), int(width * 0.775), int(height * 0.62)))
    # Make it 2x bigger than we show it so it looks sharp on a Mac Retina screen
    logo = logo.resize((size * 3, size * 3), Image.LANCZOS)
    # Cut the square into a circle by making the corners see-through
    circle_mask = Image.new("L", logo.size, 0)
    ImageDraw.Draw(circle_mask).ellipse((0, 0, logo.size[0] - 1, logo.size[1] - 1), fill=255)
    logo.putalpha(circle_mask)
    # CTkImage shows our picture at the size we ask for
    return ctk.CTkImage(light_image=logo, dark_image=logo, size=(size, size))
