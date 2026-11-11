# This file holds everything to do with our app logo
# To be able to build the path to our logo file
import os
# customtkinter shows our logo in the app
import customtkinter as ctk
# Pillow lets us open, crop and resize our logo image so customtkinter can show it
# ImageFont and ImageFilter are new: we use them to draw our glowing VORTEXA name
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from theme import theme, colors, brand, fonts_folder

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


# NEW: Draw the "VORTEXA" name as a picture with a soft orange glow.
# Why a picture? Tkinter on a Mac cannot load a custom font file (like Orbitron) directly,
# but Pillow can. So we draw the text with Pillow and show it as an image.
# height is how tall the name will be on the screen, for example load_wordmark(34)
def load_wordmark(height):
    scale = 3  # draw 3x bigger than we show it so it stays sharp on Retina screens
    font_file = os.path.join(fonts_folder, theme.get("font", {}).get("wordmark_file", "Orbitron-800.ttf"))
    wordmark_font = ImageFont.truetype(font_file, height * scale)

    white_part = brand.get("name_white", "VORT")
    orange_part = brand.get("name_orange", "EXA")
    glow_size = 6 * scale  # extra room around the text for the glow

    # Measure the text so our picture is exactly big enough
    white_width = wordmark_font.getbbox(white_part)[2]
    total_width = white_width + wordmark_font.getbbox(orange_part)[2]
    text_top, text_bottom = wordmark_font.getbbox(white_part + orange_part)[1::2]
    picture_size = (total_width + glow_size * 2, text_bottom - text_top + glow_size * 2)
    text_position = (glow_size, glow_size - text_top)

    # Step 1: draw the whole name in orange, then blur it. This blurry copy is our "glow".
    glow = Image.new("RGBA", picture_size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).text(text_position, white_part + orange_part, font=wordmark_font, fill=colors.get("primary", "#FF731C"))
    glow = glow.filter(ImageFilter.GaussianBlur(4 * scale))
    # Make the glow a bit see-through so it is soft, not loud
    glow.putalpha(glow.getchannel("A").point(lambda alpha: int(alpha * 0.55)))

    # Step 2: draw the sharp text on top: first part white, second part orange
    sharp_text = Image.new("RGBA", picture_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(sharp_text)
    draw.text(text_position, white_part, font=wordmark_font, fill=colors.get("text", "#F2F6F5"))
    draw.text((text_position[0] + white_width, text_position[1]), orange_part, font=wordmark_font, fill=colors.get("primary", "#FF731C"))

    # Step 3: stack the sharp text on top of the glow
    wordmark = Image.alpha_composite(glow, sharp_text)
    return ctk.CTkImage(light_image=wordmark, dark_image=wordmark,
                        size=(picture_size[0] // scale, picture_size[1] // scale))
