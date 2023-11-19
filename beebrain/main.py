### ----------------------------------------------------------
### Imports
### ----------------------------------------------------------
import flet as ft

import psutil, platform

import datetime, time

from tools import llm, common, image
import json

from tools.browser import quick_search, copilot, scrape_url
from tools.image import image_gen

### ----------------------------------------------------------
### Settings
### ----------------------------------------------------------
settings = {"image": [{"model": "sd-xl", "quality": "medium"}]}

### ----------------------------------------------------------
### functions
### ----------------------------------------------------------

def change_image_model(model: str, settings):
    settings["image"][0]["model"] = model
    return settings

def change_image_quality(quality: str, settings):
    settings["image"][0]["quality"] = quality
    return settings

def parse_llm_names():
    llms = llm.get_llms()

    human_names = []
    for model in llms:
        human_name = llms[model][0]["human_name"]
        human_names.append(human_name)

    return human_names

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
        self.llm_model_dropdown = ft.Dropdown(width=200, options=[], label="LLM Model")
        self.tools_list = ft.Column(controls=[], width=200)
        self.settings_list = ft.ListView()

        self.image_model_dropdown = ft.Dropdown(width=200, options=[], label="Image Model", on_change=lambda _: setattr(self, 'settings', change_image_model(self.image_model_dropdown.value, settings)))
        self.image_quality_dropdown = ft.Dropdown(width=200, options=[ft.dropdown.Option("Low"), ft.dropdown.Option("Medium"), ft.dropdown.Option("High")], label="Image Quality", value="Medium", on_change=lambda _: setattr(self, 'settings', change_image_quality(self.image_quality_dropdown.value, settings)))

        self.chat = ft.Column([], scroll="auto", horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.text_input = ft.TextField(label="Type your message here...", multiline=True, expand=True)
        self.send_button = ft.IconButton(icon=ft.icons.SEND_ROUNDED, on_click=self.send_message)

        self.file_selector = ft.FilePicker()
        self.file_selector_button = ft.IconButton(icon=ft.icons.ATTACH_FILE_ROUNDED, on_click=lambda _: self.file_selector.pick_files(allow_multiple=True, dialog_title="Select files to upload"))

        self.center_width = 800

    def build_ui(self, page):
        # Initialize agent dropdown
        agents = common.get_agents()
        for i, agent in enumerate(agents):
            if i == 0:
                self.agent_dropdown.value = agents[agent]["name"]
            self.agent_dropdown.options.append(ft.dropdown.Option(agents[agent]["name"]))

        # Initialize LLM model dropdown
        llm_names = parse_llm_names()
        for name in llm_names:
            self.llm_model_dropdown.options.append(ft.dropdown.Option(name))
        self.llm_model_dropdown.value = llm_names[0] if llm_names else ""

        # Initialize image model dropdown:
        self.image_model_dropdown.options.append(ft.dropdown.Option("sd-xl"))
        self.image_model_dropdown.options.append(ft.dropdown.Option("dalle-3"))
        self.image_model_dropdown.value = "sd-xl"

        # Initialize tools list
        all_tools = parse_tools()
        for each in all_tools:
            self.tools_list.controls.append(ft.Checkbox(label=each["label"], value=False, key=each["value"]))

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
            content=ft.Column([self.llm_model_dropdown, ft.Divider(height=9, thickness=3), ft.Text("Enabled Tools ⚒️"), self.tools_list, ft.Divider(height=9, thickness=3),  self.image_model_dropdown, self.image_quality_dropdown, ft.Divider(height=9, thickness=3), self.settings_list], width=self.center_width),
            width=200, bgcolor=ft.colors.BLACK, margin=ft.margin.all(2)
        )

        page.add(ft.Row([left, center, right], expand=True))

    def send_message(self, e):
        # Add the message to the chat
        input_text = self.text_input.value
        print(input_text)  # Debugging

        if not input_text:
            return
        
        ### -------------------------------------
        ### Getting tools to use 
        ### -------------------------------------

        # Get the tools
        tools = []
        for tool in self.tools_list.controls:
            print(tool.value, tool.key, tool.label)
            if tool.value:
                tools.append(tool.key)

        # Check if tools is empty
        if not tools:
            tools = None


        ### -------------------------------------
        ### Adding User message to chat
        ### -------------------------------------

        # Create the message row with avatar and user label
        message_header = ft.Container(
            content=ft.Row([
                ft.CircleAvatar(content=ft.Icon(ft.icons.PERSON_ROUNDED), bgcolor=ft.colors.AMBER, color=ft.colors.WHITE),
                ft.Markdown("### User", selectable=False)
            ]),
            width=self.center_width
        )

        # Create the Markdown component for the message
        message_body = ft.Markdown(
            value=input_text,  # Use the input text here
            selectable=False,
            code_theme="atom-one-dark",
            code_style=ft.TextStyle(font_family="Roboto Mono"),
            width=self.center_width,
        )

        # Combine into a single message container
        message_container = ft.Container(
            content=ft.Column([
                message_header,
                message_body
            ]),
            width=self.center_width
        )

        # Append the message container to the chat
        self.chat.controls.append(message_container)

        # Clear the text input field and update UI components
        self.text_input.value = ""
        self.text_input.update()
        self.chat.update()

        ### -------------------------------------
        ### Getting LLM response
        ### -------------------------------------

        # Get the LLM model name
        llm_model = self.llm_model_dropdown.value
        if not llm_model:
            return
        
        # Get system name of the LLM model
        llms = llm.get_llms()

        def find_parent(json_obj, target_value, parent=None):
                if isinstance(json_obj, dict):
                        for key, value in json_obj.items():
                                if value == target_value:
                                        return parent
                                else:
                                        result = find_parent(value, target_value, parent=json_obj)
                                        if result is not None:
                                                return result
                elif isinstance(json_obj, list):
                        for item in json_obj:
                                result = find_parent(item, target_value, parent=json_obj)
                                if result is not None:
                                        return result

                return None

        llm_model = find_parent(llms, llm_model)
        llm_model = llm_model[0]["system_name"]
        print(llm_model)

        agent = self.agent_dropdown.value
        agents = common.get_agents()
        
        def get_internal_name(agents, agent_name):
            for agent in agents.values():
                if agent['name'] == agent_name:
                    return agent['internal_name']
            return None

        internal_name = get_internal_name(agents, agent)
        print(internal_name)

        # Setup the chat history
        chat_history = setup_chat_history(internal_name)

        chat_history.append({
            "role": "user",
            "content": input_text
        })

        # Get the LLM response
        llm_response = llm.call_llm(llm_model, chat_history, 0.7, tools, settings)
        print(llm_response)

        ### -------------------------------------
        ### Adding LLM response to chat
        ### -------------------------------------

        parsed_llm_response = []
        for part in llm_response: 
             if part["role"] == "assistant":
                if part["content"] != None:
                    parsed_llm_response.append(part)
        
        print(parsed_llm_response)

        for part in parsed_llm_response:
            # Create the message row with avatar and user label
            message_header = ft.Container(
                content=ft.Row([
                    ft.CircleAvatar(content=ft.Text("🐝"), bgcolor=ft.colors.AMBER, color=ft.colors.WHITE),
                    ft.Markdown("### BeeBrain", selectable=False)
                ]),
                width=self.center_width
            )

            # Create the Markdown component for the message
            message_body = ft.Markdown(
                value=part["content"],  # Use the input text here
                selectable=False,
                code_theme="atom-one-dark",
                code_style=ft.TextStyle(font_family="Roboto Mono"),
                width=self.center_width,
            )

            # Combine into a single message container
            message_container = ft.Container(
                content=ft.Column([
                    message_header,
                    message_body
                ]),
                width=self.center_width
            )

            # Append the message container to the chat
            self.chat.controls.append(message_container)
            self.chat.update()



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