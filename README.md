# Overview of BeeBrain
BeeBrain is an advanced, multi-functional chatbot designed for users who seek a comprehensive digital assistant. It combines state-of-the-art machine learning models with a range of interactive tools to provide a versatile and user-friendly experience. Whether you're looking to run complex code, search the web efficiently, generate images, or simply engage in a conversation, BeeBrain is equipped to meet a wide array of needs.

## Key Features:
- **Diverse Toolset**: Includes a web browser, image generator, text/PDF analyzer, file browser, Jupyter Notebook, and more.
- **Advanced Chat Interface**: Utilizes modern Large Language Models (LLMs) for seamless interaction.
- **Customizability**: Designed for users who enjoy tweaking and extending functionality through Python coding.
- **Future-Ready**: Plans for integrating Vision with GPT-4-Turbo and other cutting-edge features.

## General Note
BeeBrain is primarily targeted at users with a technical background, particularly those comfortable with Python programming. It's not an 'out-of-the-box' solution for end-users but a framework for building and customizing your own chatbot.

# Chat Interface Capabilities
BeeBrain's core functionality is accessible through an intuitive LLM chat interface, supporting various models and features.

## Supported Models
### With Function Calling
- **GPT-4-Turbo (with and without Vision)**: The latest model with enhanced capabilities, including vision (coming soon).
- **GPT-3.5-Turbo-1106**: A robust model offering a balance of performance and efficiency.

### Without Function Calling
- **Claude 2.1, Claude 2, Claude Instant v1, PPLX 70B Online, Nous-hermes-llama2-70b, Phind-codellama-34b, Zephyr-7b-beta, Toppy-m-7b**: These models offer diverse functionalities but lack tool integration.

## Vision Integration
Using the Vision tool all tool calling LLM's are able to see.

# Available Tools
BeeBrain comes with an assortment of tools, each designed to enhance the user experience in unique ways.

## Current Tools
- **Browser**: Enables web searches and website scraping.
- **Image Generation**: Powered by DALLE-3 or SD-XL for high-quality image creation.
- **Vision**: Enables all models to see using GPT-4-Vison and Llava-13b
- **Jupyter Notebook**: Facilitates running and testing Python code.
- **File Browser**: LLM can see which files have been uploaded and been created. 

## Tools in Development
- **Text/PDF Analysis & Summary**: For efficient document handling.
- **Paper Search**: Assists in academic research.
- **Wolfram|Alpha**: Provides expert knowledge and computations.
- **Audio Generation**: For creating voiceovers and sound effects.

# Roadmap 
This roadmap isn't an absolute truth, more some guidelines and goals.

## Version 0.1.0
- [x] Chatting with different LLMs
- [x] Chat history
- [x] Tool support
- [x] Tools: Vision, Image Generation, Python, Web Browser
- [x] Mission Support (Characters, Specialists, etc.)
- [ ] Prompt Library Support
- [x] Basic Ui (Copying, Image Copying, Input & Output)
- [ ] Build ready (Windows)

## Version 0.2.0
- [ ] Tools: Text/PDF, Wolfram Alpha, Audio Generation, Video Generation
- [ ] Extended Interface: Seperate Tabs for Image Generation/Editing & Search
- [ ] Extended Interface: Chat Management, Folders, Changing names, etc.
- [ ] Extended Interface: Regenerate, Chat-Branching, Stop Generation, Better handling of adding messages to chat 
- [ ] Memory Handling: Auto, 1+Last Prompts, Summarie
- [ ] Better Missions: Individual default Tools
- [ ] Automatic Tools (automatically choose tools)
- [ ] Voice Conversations
- [ ] Better Web Search with Seperate LLM for Search Tasks and focuses (like with Vision)(Focuses: Web, Wikipedia, Academia, YouTube, Reddit)
- [ ] More Platforms: Phone UI & Android App

## Version 0.3.0
- [ ] Tools: Doc Maker (PDF, CSVs, Presentations), CodeRunner (C/C++, Go, Rust, Java...), Diagram maker
- [ ] Easy Tools: Add and modify tools within the app
- [ ] Memory Handling: Long Term Memmory 
- [ ] More Platforms: Web App, Linux App, Chrome Extention 
- [ ] ... more to come

# System Requirements
To utilize BeeBrain effectively, users need to obtain API keys from various service providers.

## Required API Keys
- **openai**: For LLM and image generation.
- **openrouter**: LLM routing.
- **replicate**: Various tools
- **stabilityai**: Image processing.
- **brave-search**: Web search functionality.
- **wolfram-alpha**: Access to Wolfram Alpha's computational engine.

# Images 
![image](https://github.com/MartianInGreen/BeeBrain/assets/24570687/1e9f0b9c-32a0-4f26-a98d-a6af892dedd8)
![image](https://github.com/MartianInGreen/BeeBrain/assets/24570687/14825e96-61e2-448c-90e2-10f928b249cb)
![image](https://github.com/MartianInGreen/BeeBrain/assets/24570687/302ca6db-d748-430c-8e99-e72fa6f04d50)


