### ---------------------------------------------------------------------
### Imports
### ---------------------------------------------------------------------

import openai
from openai import OpenAI

import json, os, sys, time, datetime, logging
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools'))
from common import get_api_keys, get_tools, get_agents

from browser import quick_search, copilot, scrape_url
from image import image_gen

### ---------------------------------------------------------------------
### functions
### ---------------------------------------------------------------------

def browser(query: str, browse_type: str):
    if browse_type == "quick_search":
        results = json.dumps(quick_search(query))
    elif browse_type == "copilot":
        results = json.dumps(copilot(query, 5))
    elif browse_type == "scrape_url":
        results = json.dumps(scrape_url(query))

    return results

def generate_image(prompt: str, number_of_images: int, image_aspect: str):
    results = image_gen("sd-xl", prompt, number_of_images, image_aspect, "normal")
    return results
    #return "./out/txt2_img_9125702721.png"

def python(code: str):
    pass

### ---------------------------------------------------------------------
### internal functions
### ---------------------------------------------------------------------

def parse_tools(tools):
    with open("beebrain/config/tools.json", "r") as file:
        file_tools = json.load(file)
    
    function_list = []
    for tool in tools:
        try: 
            function_list.append(file_tools[tool][0]["function"])
        except:
            print("Tool not found: " + tool)

    function_list = function_list[0]
    print(function_list)

    return function_list


### ---------------------------------------------------------------------
### Main
### ---------------------------------------------------------------------

def get_llms():
    # Read the config/models.json file 
    with open("beebrain/config/models.json", "r") as file:
        models = json.load(file)
    
    # Get the chat models
    chat_models = models["chat"]
    return chat_models

def call_llm(model: str, prompt_list, temperature: float, tools, settings):
    chat_models = get_llms()

    system_prompt = prompt_list[0]['content']
    system_prompt = system_prompt.replace("{{current_date}}", datetime.datetime.now().strftime('%Y-%m-%d %H:%M') + " " + time.strftime('UTC%z'))
    system_prompt = system_prompt.replace("{{llm_name}}", model)

    if tools != None:
        # Get the tool prompts
        all_tools = get_tools()
        tool_prompts = ""

        for tool in all_tools:
            for tool_name in tools:
                if tool_name == tool:
                    tool_prompts = tool_prompts + all_tools[tool][0]["prompt"] + "\n\n"

        tools = parse_tools(tools)
        system_prompt = system_prompt.replace("{{tools}}", "# Tools\n\n" + tool_prompts)

    # Get the model
    try: 
        model = chat_models[model][0]
    except:
        print("Model not found: Defaulting to GPT-3.5 Turbo")
        model = chat_models["gpt-3.5-turbo"]

    system_prompt = system_prompt.replace("{{knowledge_cutoff}}", str(model["knowledge_cutoff"]))
    prompt_list[0]['content'] = system_prompt

    model_max_tokens = model["context_size"]
    model_max_new_tokens = model["max_output_length"]
    
    # Get the API key
    provider = model["provider"]
    provider = provider.split("/")
    provider = provider[0]
    api_keys = get_api_keys()

    if provider == "openai":
        llm_api_key = api_keys["openai"]
        llm_base_url = "https://api.openai.com/v1"
        model_name = model["model_name"]
    elif provider == "openrouter":
        llm_api_key = api_keys["openrouter"]
        llm_base_url = "https://openrouter.ai/api/v1"
        provider = "openrouter"
        
        model_name = model["provider"]
        model_name = model_name.replace("openrouter/", "")

    client = OpenAI(api_key=llm_api_key, base_url=llm_base_url)

    if provider == "openrouter":
        extra_headers = {
            "HTTP-Referer": "http://localhost",
            "X-Title": "Bee Brain"
        }
    else:
        extra_headers = {}

    complete_response = []

    def send(message_list):
        print("Sending message to llm.")
        try:
            if tools is not None:
                completion = client.chat.completions.create(
                    extra_headers=extra_headers,
                    model=model_name,
                    messages=message_list,
                    stream=False,
                    max_tokens=model_max_new_tokens,
                    temperature=temperature,
                    tools=tools,
                    tool_choice="auto"
                )
            else:
                completion = client.chat.completions.create(
                    extra_headers=extra_headers,
                    model=model_name,
                    messages=message_list,
                    stream=False,
                    max_tokens=model_max_new_tokens,
                    temperature=temperature,
                )
        except Exception as e:
            logging.error(f"Error in API call: {e}")
            return []

        print("Got message from llm.")
        content = completion.choices[0].message
        tool_calls = content.tool_calls

        if tool_calls:
            print("Calling tools.")
            for tool_call in tool_calls:
                # Extract necessary data from the tool call
                tool_call_id = tool_call.id
                function_name = tool_call.function.name
                arguments_json = tool_call.function.arguments

                # Construct the tool call dictionary
                tool_call_dict = {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": tool_call_id,
                        "type": "function",
                        "function": {
                            "name": function_name,
                            "arguments": arguments_json
                        }
                    }]
                }

                # Append the dictionary to the prompt list
                prompt_list.append(tool_call_dict)
                complete_response.append(tool_call_dict)
            return run_tools(tool_calls)
        else:
            complete_response.append({
                "role": "assistant",
                "content": content.content
            })
            return complete_response
    
    def run_tools(tool_calls):
        available_functions = {
            "browser": browser,
            "generate_image": generate_image,
            "python": python,
        }

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            if function_name not in available_functions:
                logging.error(f"Function {function_name} not found")
                continue

            function_to_call = available_functions[function_name]

            try:
                function_args = json.loads(tool_call.function.arguments)
                function_response = function_to_call(**function_args)
            except Exception as e:
                logging.error(f"Error in function call {function_name}: {e}")
                continue

            prompt_list.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": function_response
            })
            complete_response.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": function_response
            })

            # Omit the recursive call to send, handle the response directly here
            # Add necessary processing of function_response if required
            print("Sending message to llm.")
            completion = client.chat.completions.create(
                extra_headers=extra_headers,
                model=model_name,
                messages=prompt_list,
                stream=False,
                max_tokens=model_max_new_tokens,
                temperature=temperature,
            )
            content = completion.choices[0].message
            print("Got message from llm.")

            complete_response.append({
                "role": "assistant",
                "content": content.content
            })
            return complete_response
    
    # ---------------------------------------------------------------------
    # Actually send the prompt
    completion = send(prompt_list)
    return completion

if __name__ == "__main__":
    content = """You are BeeBrain, an ai agent based on the LMM {{llm_name}}.
    Knowledge cutoff: {{knowledge_cutoff}}
    Current date: {{current_date}}
    User location: Germany, Rheinland-Pfalz, Wachenheim an der Weinstraße
    User device: OS: Windows 10 & AMD64
    Assume the above values to always be true.

    {{image_capability}}

    # Mission
    Be as helpful as possible.

    # Tools

    ## @browser

    ### @quick_search
    You have access to the @quick_search tool. This will search the web with the given query and return a maximum of 20 results with snippets from the webpages and urls. This is useful for quickly finding information.
    1. Your query should be at most one sentence
    2. The tool will respond and you'll get access to the full response.
    3. You should cite your sources with the corresponding url using markdown formatting. For example: [1](https://www.wikipedia.com/United_States)

    ### @copilot
    You have access to the @copilot tool. This will seach the web and return the full web pages. This is useful when you need a lot of details on a subject.

    ### @scrape_url
    You have access to the @scrape_url tool. This will return the contents of a webpage/url. This is helpful when the user has given you a webpage.

    ## @image
    You have access to the @image tool. This can be used to generate images using stable diffusion models.

    **Generation Guide:**
    1. If the description is not in English, translate it.
    2. Only output the tool request, nothing else.
    3. Prompts are best when they contain a description and comma sperated additions. For example 'A cat sitting infront of a fire, photorealistic, good picture' or 'A large group of people standing around a large fire in the forrest, watercolour painting, good picture'. (NEVER USE THE EXAMPLE PROMPTS)
    4. The first part of your prompt should be at least 2 detailed sentenced based on the user description. Do not write more than 4 sentences!
    5. You should add at least 5 comma separated additions and a MAXIMUM of 10.
    6. Do not display the images to the user in any way. They have already been shown to the user. 

    ## @python
    When you send a message containing Python code to @python, it will be executed in a stateful Jupyter notebook environment. Python will respond with the output of the execution or time out after 60.0 seconds. The drive at '/mnt/data' can be used to save and persist user files. This session is network enabled."""
    prompt = [
        {"role": "system", "content": content},
        {"role": "user", "content": "Who is the CEO of OpenAI?"},
    ]
    tools = [{
        "type": "function",
        "function": {
            "name": "browser",
            "parameters": {
                "type": "object",
                "properties": {
                    "browse_type": {
                        "type": "string",
                        "enum": ["quick_search", "copilot", "scrape_url"],
                        "description": "The type of browser tool to use."
                    },
                    "query": {
                        "type": "string",
                        "description": "The query to search for. Or the URL to scrape."
                    }
                },
                "required": ["query", "browse_type"]
            }
        }
    }, {
        "type": "function",
        "function": {
            "name": "generate_image",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The prompt to use for image generation."
                    },
                    "number_of_images": {
                        "type": "integer",
                        "description": "The number of images to generate."
                    },
                    "image_aspect": {
                        "type": "string",
                        "enum": ["square", "portrait", "landscape"],
                        "description": "The aspect ratio of the images to generate."
                    }
                },
                "required": ["prompt", "number_of_images", "image_aspect"]
            }
        }    
    }]



    #def print_to_console(print_string):
        #print("PRINTING TO CONSOLE FROM LLM!")
        #print(print_string)
        #return "Printed to console: " + print_string

    #test = call_llm("gpt-3.5-turbo", prompt, 0.7, tools)
    #print(test)
    parse_tools(["browser", "image"])

def agent_call():
    pass