# This file is the "brain" of VORTEXA. Everything that talks to the LLM lives here.
# The GUI files never touch llama_cpp directly, they only call the functions below.
# Every model in the models folder can be loaded here, one at a time.
import os
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
context_size = 1024      # n_ctx: how many tokens the model can "see" at once
max_output_tokens = 300  # stop after this many tokens to avoid infinite loops

# The loaded model lives here. None means "not loaded yet".
model = None
# The file name of the loaded model, like "Dolphin3.0-Llama3.1-8B_Q5_K_M.gguf"
model_file = None


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
def stream_response(user_prompt_input_text):
    messages = [{"role": "user", "content": user_prompt_input_text}]

    # Now lets print out to the console for debugging the text we are sending to our LLM
    print(f"Prompt to {model_file}: ", messages)

    # stream=True hands us the answer in small pieces. The model stops by itself when it
    # reaches its own end-of-answer token, or when it hits max_tokens.
    for chunk in model.create_chat_completion(messages, stream=True, max_tokens=max_output_tokens,
                                              top_k=40, top_p=0.95, repeat_penalty=1.1):
        # The first and last pieces carry no text, only bookkeeping, so we skip those
        text = chunk["choices"][0]["delta"].get("content")
        if text:
            yield text


# Count how many tokens some text uses, for the "0 / 1,024 tokens" counter under the input box
def count_tokens(text):
    if model is None or not text:
        return 0
    return len(model.tokenize(text.encode("utf-8"), add_bos=False))


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
