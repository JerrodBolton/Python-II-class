# This file is the "brain" of VORTEXA. Everything that talks to the LLM lives here.
# The GUI files never touch llama_cpp directly, they only call the functions below.
# The logic is the SAME as your original main.py: same model, same template,
# same sampling settings, same end-of-sequence check, same 300 token limit.
import os
# THis is the key to everything, the library to access the LLM
# I cannot overstate the importance of this library, it is the key to everything
from llama_cpp import Llama

# Very important, we need to set the path to the model file,
# this is the file that contains the LLM
# This can be and should be changed often to try out other models.
# #################### Change your model path here ####################
model_file = "Dolphin3.0-Llama3.1-8B_Q5_K_M.gguf"
# We build the full path from where this file lives, so the app finds the model
# even if you start it from a different folder
model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), model_file)

# Same numbers as before, now with names so the GUI can show them in the header
context_size = 1024      # n_ctx: how many tokens the model can "see" at once
max_output_tokens = 300  # stop after this many tokens to avoid infinite loops

# The loaded model lives here. None means "not loaded yet".
model = None


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
        n_ctx=context_size,  # Context size, you can adjust this based on your model's capabilities
    )


# Another BIG DEAL, This the TEMPLATE that we send to the LLM. This sounds like it does not matter much,
# but it does, it is very important to have a good prompt template. Each model has a different template.
def build_prompt(user_prompt_input_text):
    return f"<|im_start|>user\n{user_prompt_input_text}<|im_end|>\n<|im_start|>assistant\n"


# Another BIG DEAL, we generate a response from the LLM one token at a time.
# This is a "generator" function: instead of return, it uses yield.
# Every time it yields, the GUI gets one small piece of text to show on the screen,
# then the loop continues. That is how we get the "typing" effect.
def stream_response(user_prompt_input_text):
    prompt = build_prompt(user_prompt_input_text)
    input_tokens = model.tokenize(prompt.encode("utf-8"), special=True)

    # Now lets print out to the console for debugging the input text and tokens we are sending to our LLM
    print(f"Input tokens: ", input_tokens)

    # Let's put the I am done with my response part of the template here
    eos = model.token_eos()
    count = 0
    # BIG DEAL, we will use the model to generate a response to the input text
    for token in model.generate(input_tokens, top_k=40, top_p=0.95, repeat_penalty=1.1):
        # Let's stop our model from generating a response if it generates the end of sequence token, this is a BIG DEAL
        if token == eos:
            break  # Stop ths show
        # Now we will decode the token to text and hand it to the GUI
        yield model.detokenize([token]).decode("utf-8", errors="replace")
        count += 1
        if count > max_output_tokens:  # Limit the number of tokens to avoid infinite loops
            break


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
        "name": metadata.get("general.name", model_file),
        "parameters": metadata.get("general.size_label", "?"),
        "quantization": quantization_names.get(file_type, "Unknown"),
        "context_size": model.n_ctx() if model is not None else context_size,
        "max_output": max_output_tokens,
    }
