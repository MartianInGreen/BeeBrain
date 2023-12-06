import requests
import json
import os
import openai
from openai import OpenAI

# Get JSON from https://openrouter.ai/api/v1/models
# and save it to a file
def get_json():
    url = "https://openrouter.ai/api/v1/models"
    response = requests.get(url)
    data = response.json()
    with open('test/models.json', 'w') as outfile:
        json.dump(data, outfile)
    return data["data"]

def test_function_calling():
    data = get_json()

    # Get all model names 
    model_names = []
    for model in data:
        model_names.append(model["id"])

    responses = []

    for model in model_names: 
        # gets API Key from environment variable OPENAI_API_KEY
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )

        tools = [{
                "type": "function",
                "function": {
                    "name": "test_function",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "test_type": {
                                "type": "string",
                                "description": "A test string"
                            }
                        },
                        "required": ["test_type"]
                    }
                }
            }]

        completion = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": "Call the function 'test_function' with the argument 'hello world'",
                }],
            tools=tools
        )

        # Check if the model provided a tool call
        try: 
            if completion.choices[0].finish_reason == "tool_calls":
                responses.append({
                    "model": model,
                    "response": True
                })
                print("Model: " + model + " provided a function call")
            else:
                responses.append({
                    "model": model,
                    "response": False
                })
                print("Model: " + model + " did not provide a function call")
        except:
            responses.append({
                "model": model,
                "response": False
            })
            print("Model: " + model + " did not provide a function call")
    
    # Write responses to file
    with open('test/responses.json', 'w') as outfile:
        json.dump(responses, outfile)

if __name__ == "__main__":
    test_function_calling()