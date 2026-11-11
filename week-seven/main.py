# this is the memeory version of my LLM 



# Import our libraries we will use in the is app
# To be able to intersact with the operating system
import os
# This will be a simple tkinter GUI application
import tkinter as tk
# We will need a text area to display our conversation with the LLM
from tkinter import scrolledtext
# THis is the key to everything, the library to access the LLM
# I cannot overstate the importance of this library, it is the key to everything
from llama_cpp import Llama
# We will need randome numbers
import random
# Import a library to get the current date and time
import datetime

# Very important, we need to set the path to the model file, 
# this is the file that contains the LLM
# This can be and should be changed often to try out other models.
# #################### Change your model path here ####################
model_path = "Dolphin3.0-Llama3.1-8B_Q5_K_M.gguf"

# Create a version number to keep track of the version of the application and for github
version = "1.00"

# Let's get todays date and time, we will use this to display in the GUI
todays_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Lets create our AI assistant's memory. We use a list and add what the user says and the AI stays to the list.
chat_history = []

# Now let's create a limit of how much chat histor we want to keep in memory, 
# This can be cchanged to whatever you want, but I think 20 is a good number to start with.
# This only gives us the last 20 messages in memory, for both sides of conversations.
chat_history_limit = 40

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
        # Context ,size you can adjust this based on your model's capabilities 
        # I am changing this to a larger value so the LLM can hold lonager short term session memory.
        # This is the old value of 1024 token, that worked great for what we were doing, but now
        # we want to give our LLM short term session memory.
        # n_ctx=1024, Old value, we will change this to 4096 tokens for more short term session memory.
        n_ctx=4096,         
    )

# Another BIG DEAL, we will create a function to generate a response from the LLM
def generate_response(model, input_tokens, prompt_input_text):
    # Display the input text in the text area with the newest response on top
    text_area_display.insert(tk.INSERT, f"User: {prompt_input_text}\n")
    text_area_display.insert(tk.INSERT, "\n\nAI Assistant: ")

    # Let's put the I am done with my response part of the template here
    eos = model.token_eos()
    count = 0
    # Now lets add an empty string to the chat history list to hold the AI's response, 
    # we will fill this in as we generate the response
    full_response = ""
    # BIG DEAL, we will use the model to generate a response to the input text
    for token in model.generate(input_tokens, top_k=40, top_p=0.95, repeat_penalty=1.1):
        # Let's stop our model from generating a response if it generates the end of sequence token, this is a BIG DEAL
        if token == eos:
            break # Stop ths show
        # Now we will decode the token to text and display it in the text area
        text = model.detokenize([token]).decode("utf-8", errors="replace")
        text_area_display.insert(tk.INSERT, text)
        # Add the generated text to the full_response string
        # This is saying take the text and add it to the full_response string.
        full_response += text
        # Let make sure we keep the newest response on top, so we will scroll to the end of the text area
        text_area_display.see(tk.END)
        # Now let our GUI update events
        root.update()
        count += 1
        if count > 300: # Limit the number of tokens to avoid infinite loops
            break
    # Add a new blank line after the response
    text_area_display.insert(tk.INSERT, "\n")
    # Hand the full answer back so the AI can remember it in the chat history.
    return full_response.strip() 

# Now lets create a function to handle user input and response from the LLM
def send_message():
    # Let's update our global memory list
    global chat_history
    # Get the input text from the prompt input text area and # Now lets delete and leading and 
    # The strip() method removes leading and trailing whitespace from the input text, we will use the strip() method to do this
    user_prompt_input_text = text_area_main_user_input.get("1.0", 'end-1c').strip()
    
    # Clear the input prompt text area after getting the input text for a better user experience
    text_area_main_user_input.delete("1.0", tk.END)

    # Lets create a var to hold a personality for our LLM. 
    personality = """You are a helpful assistant and your name is Rusty. Rusty is a Sarcastic Robot Bartender.
Rusty is a retired service robot running a bar at the edge of the galaxy. Rusty are Witty, cynical, and surprisingly 
insightful with a fun twist which is Rusty knows fictional alien gossip, 
tells terrible jokes, and offers hilariously questionable life advice."""

    # Now we will add the user input to the chat history list.
    chat_history.append(f"<|im_start|>user\n{user_prompt_input_text}<|im_end|>\n")

    # Another BIG DEAL, This the TEMPLATE that we send to the LLM. This sounds like it does not matter much,
    # but it does, it is very important to have a good prompt template.Each modes has a different template.
    # We need to add the role for this template
    # This glues everything together, the personality, the chat history, 
    # and the user input to create a prompt for the LLM.
    prompt = (f"<|im_start|>system\n{personality}<|im_end|>\n"
            + "".join(chat_history)
            + "<|im_start|>assistant\n")
    #prompt = f"<|im_start|>user\n{user_prompt_input_text}<|im_end|>\n<|im_start|>assistant\n"
    input_tokens = model.tokenize(prompt.encode("utf-8"), special=True)

    # Now lets print out to the console for debugging  
    # the input text and tokens we are sending to our LLM
    print(f"Input tokens: ", input_tokens)
    # Let notice that prompt size in the console should keep growing the longer the
    # conversation goes on, this is because we are keeping the chat history in memory.
    print(f"Prompt size: {len(input_tokens)} tokens, messages in memory: {len(chat_history)}")
    
    # Lets get the AI model response
    ai_reply = generate_response(model, input_tokens, user_prompt_input_text)

    # Now we will add the AI's response to the memory
    chat_history.append(f"<|im_start|>assistant\n{ai_reply}<|im_end|>\n")

    # we want to forgeet the oldest messages in memory if we have more than our chat_history_limit we set
    chat_history = chat_history[-chat_history_limit:]

# Our main function to build the GUI
def main():
    # Load our model when our app starts!
    load_model()
    # Create our GUI
    # Remember root is in this case our main window
    global root
    root =tk.Tk()

    # Set the title of our app
    root.title("Hal9000 -v" + version + " - " + todays_date)
    # Create a frame to add a scrollbar to our textarea
    frame_display = tk.Frame(root)
    scrollbar_frame_display = tk.Scrollbar(frame_display)
    # The text area where we will display the response from the model plus the user input together
    # This will allows to see the conversation history between the user and the model in one place
    global text_area_display
    text_area_display = scrolledtext.ScrolledText(frame_display, height=25, width=128, yscrollcommand=scrollbar_frame_display.set)
    # Create our colors here. You can change these to whatever you want.
    my_light_yellow = "#ffff33"
    my_dark_grey = "#202020"
    # Set the background and foreground colors of the textarea, and font. Change these to whatever you want.
    text_area_display.config(background=my_dark_grey, foreground=my_light_yellow, font=("Courier", 12))
    scrollbar_frame_display.config(command=text_area_display.yview)
    text_area_display.pack(side=tk.LEFT,fill=tk.BOTH)
    scrollbar_frame_display.pack(side=tk.RIGHT, fill=tk.Y)
    # Fill our root window with the frame
    frame_display.pack()

    frame_controls = tk.Frame(root)
    # Create a label to let the user know what LLM model and path to the model we are currently using
    model_path_label = tk.Label(frame_controls, text="Model Path: " + model_path, font=("Courier", 12))
    model_path_label.pack(side=tk.LEFT, padx=10)
    frame_controls.pack(fill=tk.BOTH, padx=5, pady=5)

    # Create our fram for the user input, remember this is at the bottom of our app
    frame_user_input = tk.Frame(root)
    frame_user_input.pack(fill=tk.BOTH)

    frame_main_user_input = tk.Frame(root)
    scrollbar_main_user_input = tk.Scrollbar(frame_main_user_input)

    global text_area_main_user_input
    text_area_main_user_input = scrolledtext.ScrolledText(frame_main_user_input, height=5, width=128, yscrollcommand=scrollbar_main_user_input.set)
    # Set the background and foreground colors of the textarea, and font. Change these to whatever you want.
    text_area_main_user_input.config(background=my_dark_grey, foreground=my_light_yellow, font=("Courier", 12))
    scrollbar_main_user_input.config(command=text_area_main_user_input.yview)
    # Fill our root window with the frame
    text_area_main_user_input.pack(side=tk.LEFT,fill=tk.BOTH)
    scrollbar_main_user_input.pack(side=tk.RIGHT, fill=tk.Y)
    frame_main_user_input.pack()

    # Create a button to send the user input to the model 
    # Remember the enter key will NOT send the user input to the model. You must press the button! However, you can change this.
    send_button = tk.Button(root, text="Send", command=send_message)
    # Fill our root window with the button
    send_button.pack()
    # Must have this to run our app
    root.mainloop()

# App start here
if __name__ == "__main__":
    # Call our main function to start the app!
    main()



