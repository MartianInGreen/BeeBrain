# BeeBrain
BeeBrain is your personal chatbot. Use tools, search the web, generate images, run code and so much more!

> **General Note**: This project is not intended for "end-user" use, if you want to extend the functionality or change things you will have to change python code!

## Chat-interface
The main functions of BeeBrain are availible through a modern LLM chat interface. 

Currently the following models are supported:
- Models **with** Function calling
  - GPT-4-Turbo (with and without Vision)
  - GPT-3.5-Turbo-1106
- Models **without** Function calling (tools not availible)
  - Nous-hermes-llama2-70b
  - Phind-codellama-34b
  - Zephyr-7b-beta
  - Toppy-m-7b

Currently Vision is not yet implemented, but I plan on automatically supporting vision when GPT-4-Turbo is selected.

The current tools are availible:
- Browser (Search the web, scape websites)
- Image Generation (Using DALLE-3 or SD-XL)

Tools in development:
- Text/PDF Analysis & Summary
- File Browser  
- Jupyter Notebook (Run python code)
- Paper Search 
- Wolfram|Alpha 
- Audio Generation (Voice & effects)

## Requierements
You will need API keys for:
- openai: LLM and Image
- openrouter: LLM
- stabilityai: Image
- brave-search: Search
- wolfram-alpha: Wolfram Alpha