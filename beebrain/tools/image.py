## ai libraries
from openai import OpenAI
import openai
import replicate

import os, json, requests, base64, uuid 

import common


### ----------------------------------------------------------------------
### settings
### ----------------------------------------------------------------------
openai.api_key = common.get_api_keys()["openai"]
stability_api_key = common.get_api_keys()["stabilityai"]
os.environ["REPLICATE_API_TOKEN"] = common.get_api_keys()["replicate"]

### ----------------------------------------------------------------------
### functions
### ----------------------------------------------------------------------

def get_models():
    # load beebrain/config/models.json
    with open("config/models.json", "r") as f:
        data = json.load(f)

    image_models = data["text-to-image"]
    return image_models

        
def image_gen(model: str, image_prompt: str, number_of_images: int, image_size="square", quality="normal", chat_id = None):
    quality = quality.lower()
    # SD-XL
    if model == "sd-xl-stability" or model == "sd-xl-replicate" or model == "sd-xl-turbo":
        negative_prompt = "ugly, deformed, noisy, blurry, distorted, out of focus, bad anatomy, extra limbs, poorly drawn face, poorly drawn hands, missing fingers"

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

        if model == "sd-xl-stability":
            url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
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


            paths = []
            for i, image in enumerate(data["artifacts"]):
                with open(f'./working/{chat_id}/out/txt2img_{image["seed"]}.png', "wb") as f:
                    f.write(base64.b64decode(image["base64"]))
                    paths.append(f'sandbox://out/txt2img_{image["seed"]}.png')
            
            return paths
        elif model == "sd-xl-replicate":
            output = replicate.run(
                "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b", 
                input={
                    "prompt": image_prompt,
                    "negative_prompt": negative_prompt,
                    "width": image_width,
                    "height": image_height,
                    "num_inference_steps": interferance_steps,
                    "num_outputs": number_of_images,
                    "disable_safety_checker": True
                }
            )

            # Download images and save them to working/{chat_id}/out
            image_locations = []
            for image in output:
                print(image)
                image_uuid = str(uuid.uuid4())

                # Download images and save them to working/{chat_id}/out
                response = requests.get(image)

                with open(f'./working/{chat_id}/out/sdxl_{image_uuid}.png', 'wb') as f:
                    f.write(response.content)
                image_locations.append(f'sandbox://out/sdxl_{image_uuid}.png')

            print(image_locations)

            return image_locations 
        elif model == "sd-xl-turbo":
            output = replicate.run(
                "fofr/sdxl-turbo:6244ebc4d96ffcc48fa1270d22a1f014addf79c41732fe205fb1ff638c409267", 
                input={
                    "prompt": image_prompt,
                    "width": image_width,
                    "height": image_height,
                    "num_inference_steps": int(interferance_steps/20),
                    "num_outputs": number_of_images,
                    "agree_to_research_only": True
                }
            )
            
            image_locations = []
            for image in output:
                image_uuid = str(uuid.uuid4())
                response = requests.get(image)
                with open(f'./working/{chat_id}/out/sdxl-turbo_{image_uuid}.png', 'wb') as f:
                    f.write(response.content)
                image_locations.append(f'sandbox://out/sdxl-turbo_{image_uuid}.png')

            return image_locations


    # ----------------------------------------------------------------------------------------------
    # DALLE-3 
    if model == "dalle-3" or model == "dalle-3-hd":
        client = OpenAI()

        if number_of_images > 4:
            number_of_images = 4
        elif number_of_images < 1:
            number_of_images = 1

        if quality == "medium":
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
            prompt=image_prompt,
            size=image_size,
            quality=quality,
            n=number_of_images,
        )

        image_urls = []
        for image in response.data:
            image_urls.append(image.url)

        image_locations = []
        # Download images and save them to working/{chat_id}/out
        for i, url in enumerate(image_urls):
            response = requests.get(url)
            image_uuid = str(uuid.uuid4())
            with open(f'working/{chat_id}/out/dalle3_{image_uuid}.png', 'wb') as f:
                f.write(response.content)
            image_locations.append(f'sandbox://out/dalle3_{image_uuid}.png')

        return image_locations
    
    # ----------------------------------------------------------------------------------------------
    # DALLE-2
    # ----------------------------------------------------------------------------------------------
    if model == "dalle-2":
        client = OpenAI()

        if number_of_images > 4:
            number_of_images = 4
        elif number_of_images < 1:
            number_of_images = 1

        if quality == "low":
            quality = "256x256"
        if quality == "medium":
            image_size = "512x512"
        elif quality == "high":
            image_size = "1024x1024"
        else:
            image_size = "512x512"

        response = client.images.generate(
            model="dall-e-2",
            prompt=image_prompt,
            size=image_size,
            n=number_of_images,
        )

        image_urls = []
        for image in response.data:
            image_urls.append(image.url)

        image_locations = []
        # Download images and save them to working/{chat_id}/out
        for i, url in enumerate(image_urls):
            response = requests.get(url)
            image_uuid = str(uuid.uuid4())
            with open(f'working/{chat_id}/out/dalle2_{image_uuid}.png', 'wb') as f:
                f.write(response.content)
            image_locations.append(f'sandbox://out/dalle2_{image_uuid}.png')

        return image_locations

if __name__ == "__main__":
    # Change working directory to the directory of this file to one folder up
    print(image_gen("dalle-3", "A christmas tree in a living room", 1, "square", "normal"))