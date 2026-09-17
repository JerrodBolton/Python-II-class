#  Let's import the torch packages to do our AI
import torch
#  Let's import the transformers packages to do our AI
from transformers import AutoModelForCausalLM, AutoProcessor
#  Let's import the PIL package that let you work with images in python
from PIL import Image

model_name = "microsoft/Florence-2-base"

# Now we are you to tell the use that the model is ready to go and is loading

print("Downloading the model, this is our AI is brain I will use.")
print("This may take a while, please be patient if this is the first time you are running this code, it will download the model from the internet and store it in your local cache for future use.")


#  Let's create a processor variable to hold the AI model processor

processor = AutoProcessor.from_pretrained(model_name, trust_remote_code=True)
# here we down load the model
# than we load the model into the variable model
# we are use eager to be more compatible w/ a user's machine


model = AutoModelForCausalLM.from_pretrained(model_name,trust_remote_code=True, attn_implementation="eager")

# this is important because we are not training the model, we are just using is to make predictions. 
model.eval()

# this  is something that you need to change in your Jerrod. for the demo I am just hard coding the image path, 

# I can change this into a GUI later if I would like to make it more user friendly
image_filename= "my_picture.jpg"

# Now we get the use the image tool to open the image 
my_image = Image.open(image_filename)
# this is important b/c  some of the image maybe different formats


# Now the user know the AI has the image and is ready to make a prediction
task_command = "<MORE_DETAILED_CAPTION>"

print("The AI is now processing the image and will give you a caption of what it sees in the image.")

prepared_inputs = processor(images=my_image, text=task_command, return_tensors="pt")

# Next let ask th AI model to make a reply to the user prompt and what they are saying about the image.
# Also we give a set of rules and that is what the model will use to make the rely that we ask for. 
# Rules
# Don't do any wild guessing 
with torch.no_grad():
    # run the generated method & save the out to a variable called output
    generated_ids = model.generate(input_ids=prepared_inputs["input_ids"],
#  this is where the rules are applied to the model to make sure it does not do any wild guessing
pixel_values=prepared_inputs["pixel_values"], max_new_tokens=512, do_sample=False)

# now resuse the processor to convert the output numbers back into text that we humans can read.
raw_text_output = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

# Cleanup the final output
final_result = processor.post_process_generation(raw_text_output, task=task_command,                            
                                                 image_size=(my_image.width, my_image.height))

# print a blank line for better readability
print("\n")
# print the final result to the user
print("The AI has finished processing the image and here is what it sees in the image:")
print(final_result[task_command])




