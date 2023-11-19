import yaml, json

def get_api_keys():
    # Read the config/auth.yaml file 
    with open("beebrain/config/auth.yaml", "r") as file:
        api_keys = yaml.safe_load(file)
    
    api_keys = api_keys["api_keys"]

    # Get the chat models
    return api_keys

def get_tools():
    # Read the config/tools.json file 
    with open("beebrain/config/tools.json", "r") as file:
        tools = json.load(file)

    return tools

def get_agents():
    # Read the config/agents.json file 
    with open("beebrain/config/agents.json", "r", encoding='utf-8') as file:
        agents = json.load(file)

    return agents
