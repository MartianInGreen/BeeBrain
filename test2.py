import time, datetime, base64
from openai import OpenAI
from beebrain.tools import common

vision_model = "gpt-4-vision-preview"
question = "Describe the image a single sentence."
image = "sandbox://test.jpg"

print("Using vision model: " + vision_model)

# Get system message
with open("beebrain/config/templates/vision.md", "r") as file:
    system_prompt = file.read()
    system_prompt = system_prompt.replace("{{llm_name}}", vision_model)
    system_prompt = system_prompt.replace("{{knowledge_cutoff}}", "2023-04")
    system_prompt = system_prompt.replace("{{current_date}}", datetime.datetime.now().strftime('%Y-%m-%d %H:%M') + " " + time.strftime('UTC%z'))

messages = [
    {
        "role": "system",
        "content": system_prompt
    }, 
    {
        "role": "user",
        "content": [
        {
            "type": "text",
            "text": question
        }
        ]
    }
]

# Encode the image
image_data = None

if image.startswith("sandbox://"):
    image_path = image.replace("sandbox://", "")

    with open(image_path, "rb") as image_file:
        image_data = base64.b64encode(image_file.read()).decode('utf-8')
        messages[1]["content"].append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{image_data}"
            }
        })

# Call the API
client = OpenAI(api_key=common.get_api_keys()["openai"])

try:
    completion = client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=messages,
                stream=False,
                max_tokens=2048,
                temperature=0.2,
                timeout=60,
            )
    
    # Get the message content from the response
    content = completion.choices[0].message.content
    print(content)
except Exception as e:
    print("Error calling API: " + str(e))