## ai libraries
from openai import OpenAI
import openai

import os, json, requests, base64

import common

### ----------------------------------------------------------------------
### settings
### ----------------------------------------------------------------------
openai.api_key = common.get_api_keys()["openai"]
stability_api_key = common.get_api_keys()["stabilityai"]

### ----------------------------------------------------------------------
### functions
### ----------------------------------------------------------------------

def get_models():
    # load beebrain/config/models.json
    with open("beebrain/config/models.json", "r") as f:
        data = json.load(f)

    image_models = data["text-to-image"]
    return image_models

        
def image_gen(model: str, image_prompt: str, number_of_images: int, image_size="square", quality="normal"):
    quality = quality.lower()
    # SD-XL
    if model == "sd-xl":
        url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"

        if quality == "low":
            interferance_steps = 20
        elif quality == "normal":
            interferance_steps = 40
        elif quality == "high":
            interferance_steps = 60
        else:
            interferance_steps = 40

        # Check for image size
        if image_size == "square":
            image_size = "1024x1024"
        elif image_size == "portrait":
            image_size = "768x1344"
        elif image_size == "landscape":
            image_size = "1344x768"

        image_size = image_size.split("x")
        image_width = int(image_size[0])
        image_height = int(image_size[1])

        if number_of_images > 4:
            number_of_images = 4
        elif number_of_images < 1:
            number_of_images = 1

        body = {
            "steps": interferance_steps,
            "width": image_width,
            "height": image_height,
            "cfg_scale": 5,
            "samples": number_of_images,
            "text_prompts": [
                {
                "text": image_prompt,
                "weight": 1
                }
            ],
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Bearer " + stability_api_key,
        }

        response = requests.post(
            url,
            headers=headers,
            json=body,
        )

        if response.status_code != 200:
            raise Exception("Non-200 response: " + str(response.text))

        data = response.json()

        # make sure the out directory exists
        if not os.path.exists("./out"):
            os.makedirs("./out")

        paths = []
        for i, image in enumerate(data["artifacts"]):
            with open(f'./out/txt2img_{image["seed"]}.png', "wb") as f:
                f.write(base64.b64decode(image["base64"]))
                paths.append(f'./out/txt2img_{image["seed"]}.png')
        
        return paths


    # ----------------------------------------------------------------------------------------------
    # DALLE-3 
    if model == "dalle-3" or model == "dalle-3-hd":
        client = OpenAI()

        if number_of_images > 4:
            number_of_images = 4
        elif number_of_images < 1:
            number_of_images = 1

        if quality == "normal":
            quality = "standard"
        elif quality == "high":
            quality = "hd"
        else:
            quality = "standard"

        if image_size == "square":
            image_size = "1024x1024"
        elif image_size == "portrait":
            image_size = "1024x1792"
        elif image_size == "landscape":
            image_size = "1792x1024"

        response = client.images.generate(
            model="dall-e-3",
            prompt="a white siamese cat",
            size="1024x1024",
            quality="standard",
            n=number_of_images,
        )

        image_urls = []
        for image in response.data:
            image_urls.append(image.url)

        return image_urls