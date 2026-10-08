# PyTorch runs the model's calculations and controls gradient tracking.
import torch  # Import PyTorch so the model can process the image and generate text.
from functools import lru_cache
# Transformers provides tools for loading the model and preparing its inputs.
from transformers import AutoModelForCausalLM, AutoProcessor  # Import the Florence-2 model and processor classes.
# Pillow (PIL) lets us open images and convert their color format.
from PIL import Image  # Import PIL so we can open and convert the selected image.

# The name identifies the pretrained model to load from Hugging Face.
model_name = "microsoft/Florence-2-base"  # Set the Hugging Face model ID to load.


@lru_cache(maxsize=1)
def get_model():
    # """Load the Florence-2 model and processor once and reuse them."""
    print("Downloading the model, this is our AI is brain I will use.")
    print("This may take a while, please be patient if this is the first time you are running this code, it will download the model from the internet and store it in your local cache for future use.")

    processor = AutoProcessor.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(model_name, trust_remote_code=True, attn_implementation="eager")
    model.eval()
    return processor, model


def analyze_image(image_filename):  # Define a function that accepts an image path and returns a caption.
    """Open an image at the supplied path and return a detailed caption."""  # Document what the function does.
    processor, model = get_model()

    # Convert the image to the three color channels the model expects: RGB.
    my_image = Image.open(image_filename).convert("RGB")  # Open the file and convert it to standard RGB color channels.

    # This Florence-2 task token requests a more detailed description.
    task_command = "<MORE_DETAILED_CAPTION>"  # Set the captioning task the model should perform.

    # Turn the task text and image into tensors (arrays used by PyTorch).
    # return_tensors="pt" requests PyTorch tensors.
    prepared_inputs = processor(  # Prepare the image and task instruction for the model.
        images=my_image,  # Pass the image to the processor.
        text=task_command,  # Pass the task command telling the model what kind of caption to create.
        return_tensors="pt"  # Ask the processor to return PyTorch tensors.
    )

    # Skip gradient tracking to save memory while making a prediction.
    with torch.no_grad():  # Disable gradient calculations because we are only generating output, not training.
        # Generate caption tokens using the task text and processed image.
        generated_ids = model.generate(  # Ask the model to generate text from the input image.
            input_ids=prepared_inputs["input_ids"],  # Send the encoded input prompt IDs.
            pixel_values=prepared_inputs["pixel_values"],  # Send the processed image features.
            # Limit the number of new tokens (pieces of text), not words.
            max_new_tokens=512,  # Allow up to 512 new tokens in the generated caption.
            # Choose tokens without random sampling.
            do_sample=False  # Use deterministic generation instead of random sampling.
        )

    # Convert token IDs to text, removing special tokens from the output.
    # batch_decode returns a list; [0] selects our single image's result.
    raw_text_output = processor.batch_decode(  # Turn generated token IDs back into readable text.
        generated_ids,  # Use the IDs created by the model.
        skip_special_tokens=True  # Ignore formatting tokens and keep only meaningful text.
    )[0]  # Take the first result because only one image was processed.

    # Let the processor interpret the text for the requested Florence-2 task.
    # Supply the original image dimensions in (width, height) order.
    final_result = processor.post_process_generation(  # Convert the raw caption into a task-specific dictionary.
        raw_text_output,  # Use the decoded text from the model.
        task=task_command,  # Tell the processor which task produced this caption.
        image_size=(my_image.width, my_image.height)  # Provide the image size for correct post-processing.
    )

    # Return just the caption stored under the task key in the result dictionary.
    # final_result is a dictionary with the task command as the key and the caption string as the value.
    # task_command is the key we used to request a detailed caption, so we extract that value.
    final_result = final_result[task_command]  # Return the detailed caption string to the caller.
    print("Final result:", final_result)  # Print the final caption for debugging purposes.
    return final_result  # Return the detailed caption string to the caller.
