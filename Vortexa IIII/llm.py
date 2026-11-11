# This file is the "brain" of VORTEXA. Everything that talks to the LLM lives here.
# The GUI files never touch llama_cpp directly, they only call the functions below.
# Every model in the models folder can be loaded here, one at a time.
import os
# The model now loads on a background thread (see main.py), so we need a lock (see model_lock below)
import threading
# THis is the key to everything, the library to access the LLM
# I cannot overstate the importance of this library, it is the key to everything
from llama_cpp import Llama

# Very important, every model file (.gguf) lives in the models folder.
# Drop any .gguf file in there (or download one from Hugging Face inside the app)
# and it shows up in the model dropdown at the top of the window.
# We build the full path from where this file lives, so the app finds the models
# even if you start it from a different folder
models_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")

# #################### The model we start with ####################
# If this file is missing we start with the first model in the models folder instead
default_model_file = "Dolphin3.0-Llama3.1-8B_Q5_K_M.gguf"

# Same numbers as before, now with names so the GUI can show them in the header
# I am changing context_size to a larger value so the LLM can hold longer short term session memory.
# The old value of 1024 tokens worked great before, but now the whole conversation has to fit in it.
context_size = 4096      # n_ctx: how many tokens the model can "see" at once
max_output_tokens = 300  # stop after this many tokens to avoid infinite loops
# How many of the most recent messages (from both sides) we keep in memory
chat_history_limit = 40

# Lets create a var to hold a personality for our LLM.
# This is sent as the "system" message before every user message, so the model always knows who it is.
personality = """You are a helpful assistant and your name is Rusty. Rusty is a Sarcastic Robot Bartender.
Rusty is a retired service robot running a bar at the edge of the galaxy. Rusty are Witty, cynical, and surprisingly
insightful with a fun twist which is Rusty knows fictional alien gossip,
tells terrible jokes, and offers hilariously questionable life advice."""

# The loaded model lives here. None means "not loaded yet".
model = None
# The file name of the loaded model, like "Dolphin3.0-Llama3.1-8B_Q5_K_M.gguf"
model_file = None
# A Lock is like a bathroom key: only one thread can hold it at a time.
# load_model() holds it while it swaps models on the worker thread. count_tokens() (main thread)
# checks for it, so it never uses a model that is half closed or half loaded.
model_lock = threading.Lock()


# Every .gguf file in the models folder, sorted A to Z.
# Half-finished downloads end in ".gguf.part", so they are left out.
def list_models():
    if not os.path.isdir(models_folder):
        return []
    return sorted(name for name in os.listdir(models_folder) if name.lower().endswith(".gguf"))


# Here is another BIG DEAL.
# Create a function to load the model, this is where we will load the LLM into memory.
# file_name is which model to load. Leave it out to load the starting model.
def load_model(file_name=None):
    global model, model_file
    if file_name is None:
        available = list_models()
        # If there are no models at all we exit the application
        if not available:
            print(f"No .gguf model files found in {models_folder}. Please add one and try again.")
            # Exit the application with a non-zero exit code to indicate an error
            exit(1)
        file_name = default_model_file if default_model_file in available else available[0]

    # "with model_lock:" takes the key, and gives it back when the block ends (even if there is an error)
    with model_lock:
        # Only one model fits in memory at a time, so free the old one before loading the new one
        if model is not None:
            model.close()
            model = None

        # If the model file is broken, Llama() raises a ValueError. main.py catches it and shows an error.
        model = Llama(
            model_path=os.path.join(models_folder, file_name),
            n_ctx=context_size,  # Context size, you can adjust this based on your model's capabilities
        )
        model_file = file_name


# Another BIG DEAL, the TEMPLATE. Each model expects the conversation wrapped in its own special tags.
# Dolphin uses <|im_start|>user ... <|im_end|>, Llama 3.2 uses <|start_header_id|>user<|end_header_id|>, and so on.
# Luckily every .gguf file carries its own template inside it, and create_chat_completion() uses it for us.
# That is what lets us switch models without rewriting this file.
#
# Another BIG DEAL, we generate a response from the LLM one token at a time.
# This is a "generator" function: instead of return, it uses yield.
# Every time it yields, the GUI gets one small piece of text to show on the screen,
# then the loop continues. That is how we get the "typing" effect.
#
# Another BIG DEAL, MEMORY. The model forgets everything between calls, so every time we send it
# the personality AND the whole conversation so far. That is how it remembers your name.
# chat_history is the conversation's list of messages from main.py, with your newest message last.
# Each one looks like: {"role": "user" or "ai", "text": "..."}
def stream_response(chat_history):
    # The personality goes first as the "system" role.
    # create_chat_completion() wraps each role in the model's own template tags for us.
    messages = [{"role": "system", "content": personality}]
    # Then the last chat_history_limit messages. The model calls its own role "assistant", not "ai".
    for message in chat_history[-chat_history_limit:]:
        role = "user" if message["role"] == "user" else "assistant"
        messages.append({"role": role, "content": message["text"]})

    # The prompt plus the answer has to fit in context_size, or llama.cpp gives an error.
    # So while it is too big, forget the oldest message (messages[1], right after the personality).
    # We always keep the personality and your newest message.
    while len(messages) > 2 and prompt_tokens(messages) + max_output_tokens > context_size:
        del messages[1]

    # Now lets print out to the console for debugging the text we are sending to our LLM
    # Notice the prompt size should keep growing the longer the conversation goes on
    print(f"Prompt to {model_file}: {prompt_tokens(messages)} tokens, messages in memory: {len(messages) - 1}")
    print(messages)

    # stream=True hands us the answer in small pieces. The model stops by itself when it
    # reaches its own end-of-answer token, or when it hits max_tokens.
    for chunk in model.create_chat_completion(messages, stream=True, max_tokens=max_output_tokens,
                                              top_k=40, top_p=0.95, repeat_penalty=1.1):
        # The first and last pieces carry no text, only bookkeeping, so we skip those
        text = chunk["choices"][0]["delta"].get("content")
        if text:
            yield text


# About how many tokens a list of messages uses. Each message also gets a few template tags
# around it (like <|im_start|>user), so we add 8 extra tokens per message to be safe.
def prompt_tokens(messages):
    return sum(count_tokens(message["content"]) + 8 for message in messages)


# Count how many tokens some text uses, for the "0 / 4,096 tokens" counter under the input box
def count_tokens(text):
    # acquire(blocking=False) tries to take the key WITHOUT waiting. If a model is loading right now
    # we get False back, so we just say 0 instead of freezing the window until the load is done.
    if not model_lock.acquire(blocking=False):
        return 0
    try:
        if model is None or not text:
            return 0
        return len(model.tokenize(text.encode("utf-8"), add_bos=False))
    finally:
        # Always give the key back
        model_lock.release()


# llama.cpp stores the quantization as a number in the model file. This table turns it into a name.
quantization_names = {
    0: "F32", 1: "F16", 2: "Q4_0", 3: "Q4_1", 7: "Q8_0", 8: "Q5_0", 9: "Q5_1",
    10: "Q2_K", 11: "Q3_K_S", 12: "Q3_K_M", 13: "Q3_K_L", 14: "Q4_K_S", 15: "Q4_K_M",
    16: "Q5_K_S", 17: "Q5_K_M", 18: "Q6_K", 32: "BF16",
}


# Read real facts about the loaded model for the header cards
# model.metadata is a dictionary that llama.cpp reads from inside the .gguf file
def model_info():
    metadata = model.metadata if model is not None else {}
    file_type = int(metadata.get("general.file_type", -1))
    return {
        "file": model_file,
        "name": metadata.get("general.name", model_file),
        "parameters": metadata.get("general.size_label", "?"),
        "quantization": quantization_names.get(file_type, "Unknown"),
        "context_size": model.n_ctx() if model is not None else context_size,
        "max_output": max_output_tokens,
    }
