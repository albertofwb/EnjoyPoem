import os
import httpx
from openai import AzureOpenAI
from config import SPEECH_CACHE_DIR
from private_config import AzureDalle3Config

os.environ["AZURE_OPENAI_ENDPOINT"] = AzureDalle3Config.ENDPOINT
os.environ['AZURE_OPENAI_API_KEY'] = AzureDalle3Config.KEY


def generate_img_with_dalle3(prompt: str, save_path: str) -> str:
    client = AzureOpenAI(
        api_version="2024-02-01",
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        azure_endpoint=os.environ['AZURE_OPENAI_ENDPOINT']
    )

    result = client.images.generate(
        model="dalle3",  # the name of your DALL-E 3 deployment
        prompt=prompt,
        n=1
    )

    # Set the directory for the stored image
    image_dir = SPEECH_CACHE_DIR

    # If the directory doesn't exist, create it
    if not os.path.isdir(image_dir):
        os.mkdir(image_dir)

    # Retrieve the generated image
    image_url = result.data[0].url  # extract image URL from response
    generated_image = httpx.get(image_url).content  # download the image
    with open(save_path, "wb") as image_file:
        image_file.write(generated_image)
    return save_path
