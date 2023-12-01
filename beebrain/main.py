### ----------------------------------------------------------
### Imports
### ----------------------------------------------------------
import flet as ft
import openai
from openai import OpenAI
from e2b import Sandbox, CodeInterpreter

import psutil, platform

import datetime, time

from tools import llm, common, image
import json, os, base64, uuid, re, sys

from tools.browser import quick_search, copilot, scrape_url
from tools.image import image_gen

### ----------------------------------------------------------
### Settings
### ----------------------------------------------------------

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

def parse_vision_names():
    llms = llm.get_visual_llms()

    vision_llms = []
    for model in llms:
        human_name = llms[model][0]["human_name"]
        system_name = llms[model][0]["model_name"]
        vision_llms.append({"label": human_name, "value": system_name})

    return vision_llms

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

def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')


### ----------------------------------------------------------
### Main
### ----------------------------------------------------------

class ChatApp(ft.UserControl):
    def __init__(self):
        self.mission_dropdown = ft.Dropdown(width=200, options=[], label="Mission")
        self.reset_button = ft.TextButton(width=200, icon=ft.icons.AUTORENEW, text="NEW CHAT", on_click=lambda _: self.clear_chat(add_to_history=True))
        self.past_chats_list = ft.ListView(expand=True)
        self.llm_model_dropdown = ft.Dropdown(width=200, options=[], label="LLM Model")
        self.vision_model_dropdown = ft.Dropdown(width=200, options=[], label="Vision Model")
        self.tools_list = ft.Column(controls=[], width=200)
        self.settings_list = ft.ListView()

        self.image_model_dropdown = ft.Dropdown(width=200, options=[], label="Image Model", on_change=lambda _: setattr(self, 'SETTING_image_model', self.image_model_dropdown.value))
        self.image_quality_dropdown = ft.Dropdown(width=200, options=[ft.dropdown.Option("Low"), ft.dropdown.Option("Medium"), ft.dropdown.Option("High")], label="Image Quality", value="Medium", on_change=lambda _: setattr(self, 'SETTING_image_quality', self.image_quality_dropdown.value))

        self.chat = ft.Column([], scroll="auto", horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.text_input = ft.TextField(label="Type your message here...", multiline=True, expand=True)
        self.send_button = ft.IconButton(icon=ft.icons.SEND_ROUNDED, on_click=self.user_send_message)

        self.search_depth_slider = ft.Slider(min=5, max=20, divisions=3, label="{value}", value=5, on_change=lambda _: setattr(self, 'SETTING_search_depth', self.search_depth_slider.value))

        self.file_selector = ft.FilePicker(on_result=self.pick_file_result)
        self.file_selector_button = ft.IconButton(icon=ft.icons.ATTACH_FILE_ROUNDED, on_click=lambda _: self.file_selector.pick_files(allow_multiple=True, dialog_title="Select files to upload"))
        self.record_audio_button = ft.IconButton(icon=ft.icons.MIC_NONE_ROUNDED)

        self.center_width = 800

        ### -------------------------------------
        ### Non UI related variables
        ### -------------------------------------
        self.llm_model_list = get_llms()

        self.chat_history = None

        self.SETTING_search_depth = 5

        self.SETTING_image_model = "sd-xl-replicate"
        self.SETTING_image_quality = "medium"

        self.chat_id = str(uuid.uuid4())

    def pick_file_result(self, e: ft.FilePickerResultEvent):
        print(e.files)

        files = []
        file_names = []

        for file in e.files:
            file_name = file.name
            file_path = file.path

            files.append({"name": file_name, "path": file_path})
            file_names.append(file_name)

        for file in files:
            file_name = file["name"]
            file_path = file["path"]

            with open(file_path, "rb") as file:
                with open("working/" + self.chat_id + "/in/" + file_name, "wb") as out_file:
                    out_file.write(file.read())
            
        self.add_message_to_chat("Uploaded files: " + str(file_names), "tool", "file_upload", {"files": file_names})

    def populate_past_chats(self):
        # Get all past chats
        past_chats = os.listdir("working")

        # reverse the list so the newest chats are on top
        past_chats.reverse()

        # Add the chats to the list
        for chat in past_chats:
            with open("working/" + chat + "/chat.json", "r") as file:
                chat = json.load(file)[0]["content"]
            short_chat = chat[:21]
            self.past_chats_list.controls.append(ft.TextButton(text=short_chat, on_click=lambda _: self.load_chat(chat_id=chat)))

        self.page.update()

    def load_chat(self, chat_id: str):
        self.clear_chat(add_to_history=True)
        # Get the chat history
        with open("working/" + chat_id + "/chat.json", "r") as file:
            chat_history = json.load(file)

        # Get the chat name
        chat_name = chat_history[0]["content"]

        # Set the chat id
        self.chat_id = chat_id

        # Clear the chat
        self.chat.controls = []

        # Add the chat name to the chat
        self.add_message_to_chat("**Chat-ID:** " + chat_name, "system", add_to_history=False)

        # Add the chat history to the chat
        for message in chat_history[0:]:
            role = message["role"]
            content = message["content"]

            if role == "user":
                self.add_message_to_chat(content, "user", add_to_history=False)
            elif role == "assistant":
                self.add_message_to_chat(content, "assistant", add_to_history=False)
            elif role == "tool":
                tool_name = message["name"]
                tool_info = message["content"]

                self.add_message_to_chat(content, "tool", tool_name, tool_info, add_to_history=False)
            elif role == "system":
                self.add_message_to_chat(content, "system")

        self.chat.update()

    def clear_chat(self, add_to_history=False):
        self.chat_history = None
        self.chat_id = datetime.datetime.now().strftime('%Y-%m-%d%H-%M-%S') + str(uuid.uuid4())
        self.chat.controls = []

        if not os.path.exists("working"):
            os.mkdir("working")

        if add_to_history == True: 
            self.past_chats_list.controls.clear()
            self.populate_past_chats()

        self.chat.update()

    def build_ui(self, page):
        # TEST RESET VALUE
        self.chat_history = None
        self.page = page

        # Initialize LLM model dropdown
        llm_names = parse_llm_names()
        for model in llm_names:
            self.llm_model_dropdown.options.append(ft.dropdown.Option(text=model["value"]))

        # This is a bug, when adding a key to a dropdown option, the set lable will not be shown but is set
        self.llm_model_dropdown.value = llm_names[1]["value"]

        # Initialize vision model dropdown:
        vision_names = parse_vision_names()
        for model in vision_names:
            self.vision_model_dropdown.options.append(ft.dropdown.Option(text=model["value"]))
        
        self.vision_model_dropdown.value = vision_names[0]["value"]

        # Initialize image model dropdown:
        self.image_model_dropdown.options.append(ft.dropdown.Option("sd-xl-stability"))
        self.image_model_dropdown.options.append(ft.dropdown.Option("sd-xl-replicate"))
        self.image_model_dropdown.options.append(ft.dropdown.Option("sd-xl-turbo"))
        self.image_model_dropdown.options.append(ft.dropdown.Option("dalle-3"))
        self.image_model_dropdown.value = "sd-xl-replicate"

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
            content=ft.Column([self.mission_dropdown, self.past_chats_list, self.reset_button]),
            width=200, bgcolor=ft.colors.BLACK, margin=ft.margin.all(2)
        )

        center = ft.Container(
            content=ft.Column([
                ft.Container(content=self.chat, expand=True),
                ft.Column([
                    ft.Row([self.file_selector_button, self.record_audio_button, self.text_input, self.send_button], alignment="end")
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, width=self.center_width)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            expand=True, padding=ft.padding.symmetric(vertical=20),
        )

        right = ft.Container(
            content=ft.Column([self.llm_model_dropdown, ft.Divider(height=9, thickness=3), ft.Text("Enabled Tools ⚒️"), self.tools_list, ft.Divider(height=9, thickness=3),  self.vision_model_dropdown, ft.Divider(height=9, thickness=3), self.image_model_dropdown, self.image_quality_dropdown, ft.Divider(height=9, thickness=3), ft.Text("Search Results"), self.search_depth_slider, ft.Divider(height=9, thickness=3), self.settings_list], width=self.center_width),
            width=200, bgcolor=ft.colors.BLACK, margin=ft.margin.all(2)
        )

        page.add(ft.Row([left, center, right], expand=True))
        page.update()
        self.clear_chat()
        self.populate_past_chats()

    def add_message_to_chat(self, message: str, sender: str, tool_name=None, tool_info=None, add_to_history=True):
        # Create the message row with avatar and user label

        if add_to_history == True:
            # check if folder with uuid name exists under working/
            if not os.path.exists("working/" + self.chat_id):
                os.mkdir("working/" + self.chat_id)
                os.mkdir("working/" + self.chat_id + "/out")
                os.mkdir("working/" + self.chat_id + "/in")

            # initialize chat.json
            if not os.path.exists("working/" + self.chat_id + "/chat.json"):
                with open("working/" + self.chat_id + "/chat.json", "w") as file:
                    json.dump([{"role": "chat_name", "content": f"{self.chat_id}"}], file)

            # Write the message to the chat history file 
            with open("working/" + self.chat_id + "/chat.json", "r") as file:
                file_chat = json.load(file)
                if tool_name == None and tool_info == None:
                    file_chat.append({"role": sender, "content": message})
                elif tool_name != None and tool_info != None:
                    file_chat.append({"role": sender, "content": message, "tool_name": tool_name, "tool_info": tool_info})
            with open("working/" + self.chat_id + "/chat.json", "w") as file:
                json.dump(file_chat, file)
            

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
                name = tool_name.capitalize()
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

                num_images = len(images)

                page_images = ft.Row(expand=False, wrap=True, width=self.center_width)

                for image in images:
                    page_images.controls.append(ft.Image(src=image, width=self.center_width/num_images))

                message = f"**Prompt**: '{tool_info['prompt']}'\n\n" + f"**Number of images**: {tool_info['number_of_images']}\n\n" + f"**Image aspect**: {tool_info['image_aspect']}\n\n" + f"**Image model**: {tool_info['image_model']}\n\n" + f"**Image quality**: {tool_info['image_quality']}\n\n"
            elif tool_name == "python":
                code = tool_info["code"]
                stdout = tool_info["stdout"]
                stderr = tool_info["stderr"]
                artifacts = tool_info["artifacts"]

                code_message = f"**Code**: \n ```python\n{code}\n```"
                message = f"**Stdout**: {stdout}\n\n" + f"**Stderr**: {stderr}\n\n"
                code_artifacts = ft.Row(expand=False, wrap=True, width=self.center_width)

                for artefact in artifacts:
                    code_artifacts.controls.append(ft.Image(src=artefact, width=self.center_width/len(artifacts)))
            elif tool_name == "file_upload": 
                files = tool_info["files"]

                files = ", ".join(files)

                message = f"**Files**: {files}\n\n"
                name = "File Upload"


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
            selectable=True,
            code_theme="atom-one-dark",
            code_style=ft.TextStyle(font_family="Roboto Mono"),
            extension_set="gitHubWeb",
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
        if tool_name and tool_info != None and tool_name == "python":
            code_message = ft.Markdown(
                value=code_message,  # Use the input text here
                selectable=True,
                code_theme="atom-one-dark",
                extension_set="gitHubWeb",
                code_style=ft.TextStyle(font_family="Roboto Mono"),
                width=self.center_width,
                on_tap_link=lambda e: self.page.launch_url(e.data),
            )

            message_container = ft.Container(
                content=ft.Column([
                    message_header,
                    code_message,
                    code_artifacts,
                    message_body,
                ]),
                width=self.center_width
            )

        # Append the message container to the chat
        self.chat.controls.append(message_container)
        self.chat.update()

    def browser(self, query: str, browse_type: str):
        if browse_type == "quick_search":
            try: 
                raw_results = quick_search(query=query, count=self.SETTING_search_depth)
                results = json.dumps(raw_results)
            except Exception as e:
                print(e)

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
        results = image_gen(self.SETTING_image_model, prompt, number_of_images, image_aspect, self.SETTING_image_quality, self.chat_id)
        self.add_message_to_chat("Used tool: " + "image", "tool", "image", {"prompt": prompt, "number_of_images": number_of_images, "image_aspect": image_aspect, "image_model": self.SETTING_image_model, "image_quality": self.SETTING_image_quality, "results": results})
        return str(results)
        #return "./out/txt2_img_9125702721.png"

    def code_interpreter(self, code: str):
        print("Code: " + code)
        sandbox = CodeInterpreter(api_key=common.get_api_keys()["e2b"])

        try: 
            stdout, stderr, artifacts = sandbox.run_python(code)
        except Exception as e:
            print("Error running python code: " + str(e))
            return "Error running python code, please try again later..."

        print("Returned Output: " + str(stdout))
        print("Returned Error: " + str(stderr))
        print("Returned Artifacts: " + str(artifacts))

        artefact_paths = []
        if artifacts:
            for artefact in artifacts:
                # save the chart to a file
                # generate random uuid to string
                uuid = str(base64.urlsafe_b64encode(os.urandom(15)), 'utf-8')

                with open("out/" + str(uuid) + ".png", 'wb') as f:
                    downloaded_chart = artefact.download()

                    # convert png bytes to a file
                    f.write(downloaded_chart)
                    artefact_paths.append("out/" + str(uuid) + ".png")

        self.add_message_to_chat("Used tool: " + "python", "tool", "python", {"code": code, "stdout": stdout, "stderr": stderr, "artifacts": artefact_paths})

        sandbox.close()

        return str(stdout)

    def vision(self, image, question: str = "Describe the image in as much detail as possible."):
        # Get Vision models
        vision_models = llm.get_visual_llms()

        # user selected model 
        #vision_model = self.vision_model_dropdown.value
        vision_model = "gpt-4-vision-preview"

        # Check if the model is available
        if vision_model not in vision_models:
            vision_model = "gpt-4-vision-preview"

        print("Using vision model: " + vision_model)
        print("Using image: " + image)

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
        if image.startswith("sandbox://"):
            image_data = None
            image_path = image.replace("sandbox://", "")

            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
                messages[1]["content"].append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_data}"
                    }
                })
        elif image.startswith("http"):
            messages[1]["content"].append({
                "type": "image_url",
                "image_url": {
                    "url": image
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
        except Exception as e:
            print("Error calling API: " + str(e))
            return "Error calling API, please try again later..."

        self.add_message_to_chat(content, "tool", "vision")

        return content

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
            "python": self.code_interpreter,
            "vision": self.vision,
        }

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            if function_name not in available_functions:
                print(f"Function {function_name} not found")
                return None

            function_to_call = available_functions[function_name]
            print(f"Calling function {function_name}...")

            try:
                function_args = json.loads(tool_call.function.arguments)
                print(function_args)
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
        prompt_list, tools, llm_api_key, llm_base_url, model_max_new_tokens, extra_headers, model_name = llm.prepare_llm_response(model=llm_model, prompt_list=self.chat_history, tools=tools, llm_model_list=self.llm_model_list)

        i = 0
        while i < 5: 
            print("Calling LLM...")
            response = self.call_llm(prompt_list, model_name, tools, 0.7, model_max_new_tokens, llm_api_key, llm_base_url, extra_headers)
            print("Got LLM response...")

            if response == None:
                self.add_message_to_chat("Error while calling LLM...", "system")
                break
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
                    print(tool_calls)
                    prompt_list = self.call_tool(tool_calls, prompt_list)
                    i += 1
                    print("Got Tool response...")
                
                # Get the message content from the response
                elif content.content:
                    message_content = content.content
                    print(message_content)

                    # replace this regex !\[.*\]\((sandbox)(.*)\) with nothing

                    message_content = re.sub(r'!\[.*\]\((sandbox)(.*)\)', '', message_content)

                    self.add_message_to_chat(message_content, "assistant")
                    prompt_list.append({
                        "role": "assistant",
                        "content": message_content
                    })
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
    #ft.app(target=main, view=ft.AppView.WEB_BROWSER)
    ft.app(target=main)
    #setup_chat_history("default")
    #parse_tools()
    #print(ChatApp.vision(ChatApp, "sandbox://test.jpg"))