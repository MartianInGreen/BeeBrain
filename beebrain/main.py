### ----------------------------------------------------------
### Imports
### ----------------------------------------------------------
import flet as ft
import openai
from openai import OpenAI

import psutil, platform

import datetime, time

from tools import llm, common, image
import json, os

from tools.browser import quick_search, copilot, scrape_url
from tools.image import image_gen

### ----------------------------------------------------------
### Settings
### ----------------------------------------------------------
settings = {"image": [{"model": "sd-xl", "quality": "medium"}], "search": [{"depth": 5}]}

### ----------------------------------------------------------
### functions
### ----------------------------------------------------------

def change_image_model(model: str, settings):
    settings["image"][0]["model"] = model
    return settings

def change_image_quality(quality: str, settings):
    settings["image"][0]["quality"] = quality
    return settings

def change_search_depth(depth: int, settings):
    settings["search"][0]["depth"] = depth
    return settings

def parse_llm_names():
    llms = llm.get_llms()

    llm_names = []
    for model in llms:
        human_name = llms[model][0]["human_name"]
        system_name = llms[model][0]["model_name"]
        llm_names.append({"label": human_name, "value": system_name})

    return llm_names

def get_llms():
    with open("beebrain/config/models.json", "r") as file:
        models = json.load(file)
    
    # Get the chat models
    chat_models = models["chat"]
    return chat_models

def get_tool_functions(tools):
    with open("beebrain/config/tools.json", "r") as file:
        file_tools = json.load(file)
    
    function_list = []
    for tool in tools:
        try: 
            function_list.append(file_tools[tool][0]["function"])
        except:
            print("Tool not found: " + tool)

    function_list = function_list[0]
    #print(function_list)

    return function_list

def parse_tools():
    tools = common.get_tools()

    # human_names = []
    # for tool in tools:
    #     human_name = tools[tool][0]["name"]
    #     human_names.append(human_name)

    tool_names = []
    for tool in tools:
        human_name = tools[tool][0]["name"]
        tool_names.append({"label": human_name, "value": tool})

    return tool_names

def setup_chat_history(agent: str):
    agents = common.get_agents()
    tools = common.get_tools()

    #read the default.md file from templates
    with open("beebrain/config/templates/default.md", "r") as file:
        system_prompt = file.read()
    
    try: 
        tool_prompts = []
        agent = agents[agent]
        for tool in agent["tools"]:
            tool_prompts.append(tools[tool][0]["prompt"])
        
        tool_prompts = "\n".join(tool_prompts)
    except:
        tool_prompts = ""

    # System settings
    system_prompt = system_prompt.replace("{{mission}}", "# Mission\n" + agent["mission"])

    # User info
    uname = platform.uname()
    device = "OS: " + uname.system + " " + uname.release + " & " + uname.machine

    system_prompt = system_prompt.replace("{{user_instructions}}", "")
    system_prompt = system_prompt.replace("{{location}}", "Germany, Rheinland-Pfalz, Wachenheim an der Weinstraße")
    system_prompt = system_prompt.replace("{{device}}", device)

    chat_history = [{
        "role": "system",
        "content": system_prompt
    }]

    return chat_history

### ----------------------------------------------------------
### Main
### ----------------------------------------------------------

class ChatApp(ft.UserControl):
    def __init__(self):
        self.agent_dropdown = ft.Dropdown(width=200, options=[], label="Agent")
        self.past_chats_list = ft.ListView()
        self.llm_model_dropdown = ft.Dropdown(width=200, options=[], label="LLM Model", value="GPT 4 Turbo")
        self.tools_list = ft.Column(controls=[], width=200)
        self.settings_list = ft.ListView()

        self.image_model_dropdown = ft.Dropdown(width=200, options=[], label="Image Model", on_change=lambda _: setattr(self, 'SETTING_image_model', {self.image_model_dropdown.value}))
        self.image_quality_dropdown = ft.Dropdown(width=200, options=[ft.dropdown.Option("Low"), ft.dropdown.Option("Medium"), ft.dropdown.Option("High")], label="Image Quality", value="Medium", on_change=lambda _: setattr(self, 'SETTING_image_quality', {self.image_quality_dropdown.value}))

        self.chat = ft.Column([], scroll="auto", horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.text_input = ft.TextField(label="Type your message here...", multiline=True, expand=True)
        self.send_button = ft.IconButton(icon=ft.icons.SEND_ROUNDED, on_click=self.user_send_message)

        self.search_depth_slider = ft.Slider(min=5, max=20, divisions=3, label="{value}", value=5, on_change=lambda _: setattr(self, 'SETTING_search_depth', {self.search_depth_slider.value}))

        self.file_selector = ft.FilePicker()
        self.file_selector_button = ft.IconButton(icon=ft.icons.ATTACH_FILE_ROUNDED, on_click=lambda _: self.file_selector.pick_files(allow_multiple=True, dialog_title="Select files to upload"))

        self.center_width = 800

        ### -------------------------------------
        ### Non UI related variables
        ### -------------------------------------
        self.llm_model_list = get_llms()

        self.chat_history = None

        self.SETTING_search_depth = 5

        self.SETTING_image_model = "sd-xl"
        self.SETTING_image_quality = "medium"

    def build_ui(self, page):
        # Initialize agent dropdown
        self.page = page
        agents = common.get_agents()
        for i, agent in enumerate(agents):
            if i == 0:
                self.agent_dropdown.value = agents[agent]["name"]
            self.agent_dropdown.options.append(ft.dropdown.Option(text=agents[agent]["name"]))

        # Initialize LLM model dropdown
        llm_names = parse_llm_names()
        set_default = False 
        for model in llm_names:
            self.llm_model_dropdown.options.append(ft.dropdown.Option(text=model["value"]))

        # This is a bug, when adding a key to a dropdown option, the set lable will not be shown but is set
        self.llm_model_dropdown.value = llm_names[0]["value"]

        # Initialize image model dropdown:
        self.image_model_dropdown.options.append(ft.dropdown.Option("sd-xl"))
        self.image_model_dropdown.options.append(ft.dropdown.Option("dalle-3"))
        self.image_model_dropdown.value = "sd-xl"

        # Initialize tools list
        all_tools = parse_tools()
        for each in all_tools:
            
            if each["value"] in ["browser", "image", "python"]:
                on_by_default = True
            else:
                on_by_default = False

            self.tools_list.controls.append(ft.Checkbox(label=each["label"], value=on_by_default, key=each["value"]))

        # Construct the UI
        page.overlay.append(self.file_selector)
        
        left = ft.Container(
            content=ft.Column([self.agent_dropdown, self.past_chats_list]),
            width=200, bgcolor=ft.colors.BLACK, margin=ft.margin.all(2)
        )

        center = ft.Container(
            content=ft.Column([
                ft.Container(content=self.chat, expand=True),
                ft.Column([
                    ft.Row([self.file_selector_button, self.text_input, self.send_button], alignment="end")
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, width=self.center_width)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            expand=True, padding=ft.padding.symmetric(vertical=20),
        )

        right = ft.Container(
            content=ft.Column([self.llm_model_dropdown, ft.Divider(height=9, thickness=3), ft.Text("Enabled Tools ⚒️"), self.tools_list, ft.Divider(height=9, thickness=3),  self.image_model_dropdown, self.image_quality_dropdown, ft.Divider(height=9, thickness=3), ft.Text("Search Results"), self.search_depth_slider, ft.Divider(height=9, thickness=3), self.settings_list], width=self.center_width),
            width=200, bgcolor=ft.colors.BLACK, margin=ft.margin.all(2)
        )

        page.add(ft.Row([left, center, right], expand=True))
        page.update()

    def add_message_to_chat(self, message: str, sender: str, tool_name=None, tool_info=None):
        # Create the message row with avatar and user label

        content = ""
        if sender == "user":
            content = ft.Icon(ft.icons.PERSON_ROUNDED)
            name = "You"
        elif sender == "assistant":
            content = ft.Text("🐝")
            name = "BeeBrain"
        elif sender == "tool":
            content = ft.Text("⚒️")
            if tool_name != None:
                name = tool_name
            else:
                name = "Tool"
        elif sender == "system":
            content = ft.Text("🤖")
            name = "System"

        if tool_name and tool_info != None:
            if tool_name == "browser":
                query = tool_info["query"]
                browse_type = tool_info["browse_type"]
                sites = tool_info["sites"]

                parse_sites = ""
                for site in sites:
                    site = "- <" + site + ">\n"
                    parse_sites = parse_sites + site

                message = f"**Search for**: '{query}' ({browse_type})\n\n" + "Found results from the following sites:\n\n" + parse_sites
            elif tool_name == "image":
                images = tool_info["results"]

                page_images = ft.Row(expand=False, wrap=True, width=self.center_width)

                for image in images:
                    print(image)
                    page_images.controls.append(ft.Image(src=image, width=self.center_width))

                message = f"**Prompt**: '{tool_info['prompt']}'\n\n" + f"**Number of images**: {tool_info['number_of_images']}\n\n" + f"**Image aspect**: {tool_info['image_aspect']}\n\n" + f"**Image model**: {tool_info['image_model']}\n\n" + f"**Image quality**: {tool_info['image_quality']}\n\n"
                

        message_header = ft.Container(
            content=ft.Row([
                ft.CircleAvatar(content=content, bgcolor=ft.colors.AMBER, color=ft.colors.WHITE),
                ft.Markdown(f"### {name}", selectable=False)
            ]),
            width=self.center_width
        )

        # Create the Markdown component for the message
        message_body = ft.Markdown(
            value=message,  # Use the input text here
            selectable=False,
            code_theme="atom-one-dark",
            code_style=ft.TextStyle(font_family="Roboto Mono"),
            width=self.center_width,
            on_tap_link=lambda e: self.page.launch_url(e.data),
        )

        # Combine into a single message container
        message_container = ft.Container(
            content=ft.Column([
                message_header,
                message_body
            ]),
            width=self.center_width
        )

        if tool_name and tool_info != None and tool_name == "image":
            message_container = ft.Container(
                content=ft.Column([
                    message_header,
                    message_body,
                    page_images
                ]),
                width=self.center_width
            )

        # Append the message container to the chat
        self.chat.controls.append(message_container)
        self.chat.update()

    def browser(self, query: str, browse_type: str):
        if browse_type == "quick_search":
            raw_results = quick_search(query=query, count=self.SETTING_search_depth)
            results = json.dumps(raw_results)

            try: 
                sites = []
                for result in raw_results:
                    sites.append(result["url"])

                additional_info = [{"query": query, "browse_type": browse_type, "sites": sites}]
                additional_info = additional_info[0]

                self.add_message_to_chat("Used tool: " + "browser", "tool", "browser", additional_info)
            except Exception as e:
                self.add_message_to_chat("Used tool: " + "browser", "tool", "browser")
                print(e)               
        elif browse_type == "copilot":
            raw_results = copilot(query, 5)
            result = json.dumps(raw_results)

            try: 
                sites = []
                for result in raw_results:
                    sites.append(result["url"])

                additional_info = [{"query": query, "browse_type": browse_type, "sites": sites}]
                additional_info = additional_info[0]

                self.add_message_to_chat("Used tool: " + "browser", "tool", "browser", additional_info)
            except:
                self.add_message_to_chat("Used tool: " + "browser", "tool", "browser")
        elif browse_type == "scrape_url":
            results = json.dumps(scrape_url(query))

            self.add_message_to_chat("Scraped URL: " + {query}, "tool", "browser")

        return results

    def generate_image(self, prompt: str, number_of_images: int, image_aspect: str):
        results = image_gen(self.SETTING_image_model, prompt, number_of_images, image_aspect, self.SETTING_image_quality)
        self.add_message_to_chat("Used tool: " + "image", "tool", "image", {"prompt": prompt, "number_of_images": number_of_images, "image_aspect": image_aspect, "image_model": self.SETTING_image_model, "image_quality": self.SETTING_image_quality, "results": results})
        return str(results)
        #return "./out/txt2_img_9125702721.png"

    def python(code: str):
        pass

    def call_llm(self, prompt_list, model_name, tools, temperature: int, max_new_tokens: int, llm_api_key: str, llm_base_url: str, extra_headers):
        client = OpenAI(api_key=llm_api_key, base_url=llm_base_url)

        try: 
            if tools is not None:
                completion = client.chat.completions.create(
                    extra_headers=extra_headers,
                    model=model_name,
                    messages=prompt_list,
                    stream=False,
                    max_tokens=max_new_tokens,
                    temperature=temperature,
                    tools=tools,
                    timeout=60,
                    tool_choice="auto"
                )
            else:
                completion = client.chat.completions.create(
                    extra_headers=extra_headers,
                    model=model_name,
                    messages=prompt_list,
                    stream=False,
                    max_tokens=max_new_tokens,
                    timeout=60,
                    temperature=temperature,
                )
            return completion
        except Exception as e:
            print("Error calling API: " + str(e))
            return None

    def call_tool(self, tool_calls, prompt_list):
        available_functions = {
            "browser": self.browser,
            "generate_image": self.generate_image,
            "python": self.python,
        }

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            if function_name not in available_functions:
                print(f"Function {function_name} not found")
                return None

            function_to_call = available_functions[function_name]

            try:
                function_args = json.loads(tool_call.function.arguments)
                function_response = function_to_call(**function_args)
            except Exception as e:
                print(f"Error in function call {function_name}: {e}")
                return None

            prompt_list.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": function_response
            })

        return prompt_list

    def user_send_message(self, e):
        # -------------------------------------
        # User Input
        # -------------------------------------
        # Add the message to the chat
        input_text = self.text_input.value

        if not input_text:
            return
        
        self.add_message_to_chat(input_text, "user")

        # Clear the text input field and update UI components
        self.text_input.value = ""
        self.text_input.update()
        self.chat.update()
        
        ### -------------------------------------
        ### Getting tools & llm
        ### -------------------------------------

        # Get the tools
        tools = []
        for tool in self.tools_list.controls:
            if tool.value:
                tools.append(tool.key)

        # Check if tools is empty
        if not tools:
            tools = None

        llm_model = self.llm_model_dropdown.value

        ### -------------------------------------
        ### Setting chat history
        ### -------------------------------------

        if self.chat_history == None:
            with open("beebrain/config/templates/default.md", "r") as file:
                system_prompt = file.read()
            
            uname = platform.uname()
            device = "OS: " + uname.system + " " + uname.release + " & " + uname.machine

            system_prompt = system_prompt.replace("{{user_instructions}}", "")
            system_prompt = system_prompt.replace("{{location}}", "Germany, Rheinland-Pfalz, Wachenheim an der Weinstraße")
            system_prompt = system_prompt.replace("{{device}}", device)

            self.chat_history = [{
                "role": "system",
                "content": system_prompt
            }]

            self.chat_history.append({
                "role": "user",
                "content": input_text
            })
        else:
            self.chat_history.append({
                "role": "user",
                "content": input_text
            })
        
        ### -------------------------------------
        ### Getting LLM response
        ### -------------------------------------
        prompt_list, tools, llm_api_key, llm_base_url, model_max_new_tokens, extra_headers = llm.prepare_llm_response(model=llm_model, prompt_list=self.chat_history, tools=tools, llm_model_list=self.llm_model_list)

        i = 0
        while i < 5: 
            print("Calling LLM...")
            print(prompt_list)
            response = self.call_llm(prompt_list, llm_model, tools, 0.7, model_max_new_tokens, llm_api_key, llm_base_url, extra_headers)
            print("Got LLM response...")

            if response == None:
                self.add_message_to_chat("Error while calling LLM...", "system")
                i += 1 
            else:
                content = response.choices[0].message
                tool_calls = content.tool_calls

                if tool_calls:
                    print("Calling Tool...")
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

                        # Add the tool call to the prompt list
                        prompt_list.append(tool_call_dict)
                
                    # Call the tools
                    prompt_list = self.call_tool(tool_calls, prompt_list)
                    i += 1
                    print("Got Tool response...")
                
                # Get the message content from the response
                elif content.content:
                    message_content = content.content
                    self.add_message_to_chat(message_content, "assistant")
                    i += 1 
                    break


def main(page: ft.Page):
    app = ChatApp()
    app.build_ui(page)

### ---------------------------------------------------------------------
### Tools
### ---------------------------------------------------------------------

### ----------------------------------------------------------
### Run
### ----------------------------------------------------------


if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER)
    #ft.app(target=main)
    #setup_chat_history("default")
    #parse_tools()