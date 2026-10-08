# Import our libraries we will use in the is app
# To be able to intersact with the operating system
import os
# We still use tkinter for a few constants like tk.END and tk.INSERT
import tkinter as tk
# customtkinter gives our app a modern look, it is built on top of tkinter
import customtkinter as ctk
# THis is the key to everything, the library to access the LLM
# I cannot overstate the importance of this library, it is the key to everything
from llama_cpp import Llama
# We will need randome numbers
import random
# Import a library to get the current date and time
import datetime
# We will read our colors and fonts from a json file in our assets folder
import json
# Our logo lives in its own file, logo.py
from logo import load_logo

# Very important, we need to set the path to the model file, 
# this is the file that contains the LLM
# This can be and should be changed often to try out other models.
# #################### Change your model path here ####################
model_path = "Dolphin3.0-Llama3.1-8B_Q5_K_M.gguf"

# Create a version number to keep track of the version of the application and for github
version = "1.00"

# Our assets folder holds our theme (colors, fonts), images, icons and fonts
# We build the path from where main.py lives so it works no matter where we start the app from
assets_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
images_folder = os.path.join(assets_folder, "images")
icons_folder = os.path.join(assets_folder, "icons")
fonts_folder = os.path.join(assets_folder, "fonts")

# Load our theme from assets/theme.json, change the colors and fonts in that file, not here
with open(os.path.join(assets_folder, "theme.json")) as theme_file:
    theme = json.load(theme_file)

# Let's get todays date and time, we will use this to display in the GUI
todays_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Here is another BIG DEAL.
# Create a function to load the model, this is where we will load the LLM into memory
def load_model():
    # First we will check if the model file exists, if it does not exist we will exit the application
    if not os.path.exists(model_path):
        print(f"Model file not found at {model_path}. Please check the path and try again.")
        # Exit the application with a non-zero exit code to indicate an error that the model
        # was not found at the specified path
        exit(1)

    # If the model file exists, we will try to load the model into memory.
    global model
    model = Llama(
        model_path=model_path,
        n_ctx=1024,  # Context size, you can adjust this based on your model's capabilities        
    )

# Another BIG DEAL, we will create a function to generate a response from the LLM
def generate_response(model, input_tokens, prompt_input_text):
    # Display the input text in the text area with the newest response on top
    text_area_display.insert(tk.INSERT, f"User: {prompt_input_text}\n")
    text_area_display.insert(tk.INSERT, "\n\nAI Assistant: ")

    # Let's put the I am done with my response part of the template here
    eos = model.token_eos()
    count = 0
    # BIG DEAL, we will use the model to generate a response to the input text
    for token in model.generate(input_tokens, top_k=40, top_p=0.95, repeat_penalty=1.1):
        # Let's stop our model from generating a response if it generates the end of sequence token, this is a BIG DEAL
        if token == eos:
            break # Stop ths show
        # Now we will decode the token to text and display it in the text area
        text = model.detokenize([token]).decode("utf-8", errors="replace")
        text_area_display.insert(tk.INSERT, text)
        # Let make sure we keep the newest response on top, so we will scroll to the end of the text area
        text_area_display.see(tk.END)
        # Now let our GUI update events
        root.update()
        count += 1
        if count > 300: # Limit the number of tokens to avoid infinite loops
            break
    # Add a new blank line after the response
    text_area_display.insert(tk.INSERT, "\n") 


# Now lets create a function to handle user input and response from the LLM
def send_message():
    # Get the input text from the prompt input text area and # Now lets delete and leading and 
    # The strip() method removes leading and trailing whitespace from the input text, we will use the strip() method to do this
    user_prompt_input_text = text_area_main_user_input.get("1.0", 'end-1c').strip()
    
    # Clear the input prompt text area after getting the input text for a better user experience
    text_area_main_user_input.delete("1.0", tk.END)

    # now lets's encode the message with utf-8 and then convert it to tokens using the model's tokenizer
    # byte_message = user_prompt_input_text.encode("utf-8")

    # Another BIG DEAL, This the TEMPLATE that we send to the LLM. This sounds like it does not matter much,
    # but it does, it is very important to have a good prompt template.Each modes has a different template.
    prompt = f"<|im_start|>user\n{user_prompt_input_text}<|im_end|>\n<|im_start|>assistant\n"
    input_tokens = model.tokenize(prompt.encode("utf-8"), special=True)

    # Now lets print out to the console for debugging  the input text and tokens we are sending to our LLM
    print(f"Input tokens: ", input_tokens)

    # Now we will call the generate_response function to get a response from the LLM
    generate_response(model, input_tokens, user_prompt_input_text)

# This function runs when the user presses the Enter key in the input box
def enter_key_pressed(event):
    # Shift+Enter still makes a new line, so the user can type more than one line
    if event.state & 0x1:
        return
    send_message()
    # Return "break" so the Enter key does not also add a new line to the input box
    return "break"

# Our main function to build the GUI
def main():
    # Load our model when our app starts!
    load_model()
    # Set the look of our app, "dark", "light" or "system" (follows your Mac's setting)
    ctk.set_appearance_mode(theme.get("appearance_mode", "dark"))
    # Set the default color of our widgets, "blue", "green" or "dark-blue"
    # Our own colors from theme.json are used on top of this
    ctk.set_default_color_theme(theme.get("button_color_theme", "blue"))

    # Get our colors and font from the theme we loaded from assets/theme.json
    # .get() gives us a default value if a setting is missing from theme.json, so the app does not crash
    colors = theme.get("colors", {})
    color_background = colors.get("background", "#202020")
    color_sidebar = colors.get("sidebar", color_background)
    color_surface = colors.get("surface", color_background)
    color_text = colors.get("text", "#ffffff")
    color_text_muted = colors.get("text_muted", color_text)
    color_primary = colors.get("primary", "#ff8c00")
    color_primary_hover = colors.get("primary_hover", color_primary)
    color_text_on_primary = colors.get("text_on_primary", color_text)
    color_border = colors.get("border", color_primary)
    color_chat = colors.get("chat_ai", color_background)
    color_input = colors.get("input_background", color_background)
    font_settings = theme.get("font", {})
    my_font = (font_settings.get("family", "Courier"), font_settings.get("size", 14))

    # Create our GUI
    # Remember root is in this case our main window
    global root
    root = ctk.CTk(fg_color=color_background)

    # Set the title of our app
    root.title("VORTEXA -v" + version + " - " + todays_date)
    root.geometry(theme.get("window_size", "1100x750"))

    # Create our header bar at the top of our app with our logo and app name
    frame_header = ctk.CTkFrame(root, fg_color=color_sidebar, corner_radius=0)
    # Our round logo on the left side of the header
    logo_label = ctk.CTkLabel(frame_header, text="", image=load_logo(56))
    logo_label.pack(side=tk.LEFT, padx=(15, 10), pady=10)
    # A frame to stack the app name on top of the subtitle
    frame_header_text = ctk.CTkFrame(frame_header, fg_color="transparent")
    app_name_label = ctk.CTkLabel(frame_header_text, text="VORTEXA", font=(my_font[0], 26, "bold"), text_color=color_primary)
    app_name_label.pack(anchor="w")
    app_subtitle_label = ctk.CTkLabel(frame_header_text, text="Local AI Assistant  -  v" + version, font=(my_font[0], 13), text_color=color_text_muted)
    app_subtitle_label.pack(anchor="w")
    frame_header_text.pack(side=tk.LEFT, pady=10)
    # Fill the whole width of our window with the header
    frame_header.pack(fill=tk.X)

    # Create a frame to hold our conversation textarea
    frame_display = ctk.CTkFrame(root, fg_color=color_surface)
    # The text area where we will display the response from the model plus the user input together
    # This will allows to see the conversation history between the user and the model in one place
    # CTkTextbox comes with its own scrollbar, so we do not need to make one
    global text_area_display
    text_area_display = ctk.CTkTextbox(frame_display, fg_color=color_chat, text_color=color_text, font=my_font, wrap="word")
    text_area_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    # Fill our root window with the frame
    frame_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 5))

    frame_controls = ctk.CTkFrame(root, fg_color="transparent")
    # Create a label to let the user know what LLM model and path to the model we are currently using
    model_path_label = ctk.CTkLabel(frame_controls, text="Model Path: " + model_path, font=my_font, text_color=color_text_muted)
    model_path_label.pack(side=tk.LEFT, padx=10)
    frame_controls.pack(fill=tk.X, padx=10, pady=5)

    # Create our frame for the user input, remember this is at the bottom of our app
    frame_main_user_input = ctk.CTkFrame(root, fg_color=color_surface, border_width=1, border_color=color_border)

    global text_area_main_user_input
    text_area_main_user_input = ctk.CTkTextbox(frame_main_user_input, height=110, fg_color=color_input, text_color=color_text, font=my_font, wrap="word",
                                               border_width=2, border_color=color_primary)
    # Make the blinking typing cursor orange and thicker so we can see where we are typing
    text_area_main_user_input._textbox.configure(insertbackground=color_primary, insertwidth=3)
    text_area_main_user_input.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    # Pressing Enter sends the message, Shift+Enter makes a new line
    text_area_main_user_input.bind("<Return>", enter_key_pressed)
    # Put the cursor in the input box when the app starts so we can start typing right away
    text_area_main_user_input.focus_set()
    frame_main_user_input.pack(fill=tk.X, padx=10, pady=5)

    # Create a button to send the user input to the model
    # You can press this button or the Enter key to send the user input to the model
    send_button = ctk.CTkButton(root, text="Send", command=send_message, font=my_font,
                                fg_color=color_primary, hover_color=color_primary_hover, text_color=color_text_on_primary)
    # Fill our root window with the button
    send_button.pack(pady=(5, 10))
    # Must have this to run our app
    root.mainloop()

# App start here
if __name__ == "__main__":
    # Call our main function to start the app!
    main()