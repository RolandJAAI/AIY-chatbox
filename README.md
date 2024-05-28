# AIY ChatBox - A Local STT, LLM, and TTS Implementation of Google AIY Voice Kit

## Overview
AIY ChatBox is a custom implementation of [Google AIY Voice Kit](https://aiyprojects.withgoogle.com/voice/). It utilizes local Speech-To-Text (STT), local Large Language Model (LLM), and local Text-To-Speech (TTS) services, all running on a MacBook or Linux-Server with GPU (recommended) within the same network. This setup is designed to work with the Google AIY Voice Kit which contains a Raspberry Pi Zero, speaker, and microphone This project is motivated by building a tutor for a personalized learning assistant experience for schools. If you do not have an AIY Box, you can run the `box_mock.py` script instead and hold the ctrl key to start and stop recording.


![ChatBox using Google AIY Voice Kit](https://github.com/RolandJAAI/chatbox/blob/main/chatbox.jpeg)

## Features
- **Local STT**: Converts speech to text using a local Whisper server.
- **Local LLM**: Processes and understands queries using an OpenAI style API ([ollama](https://ollama.com) is great).
- **Local TTS**: Converts text responses back into speech using Coqui xTTS-v2.
- **Interactive LED Indicators**: Provides visual feedback during different operations.
- **Customizable Assistant Persona**: Set up your assistant persona, with a specific interaction style.

## Prerequisites
- Google AIY Voice Kit with Raspberry Pi Zero, speaker, microphone led-button.
- MacBook (Tested on M1 64GB MAX) or any other local machine which can run the STT, LLM, and TTS services (Ubuntu server with GPU is great).
- Python >=3.7 on AIY box (update if necessary) and necessary libraries (as per the provided script).

## Server Requirements
1. **Local STT Server**: Run a local Whisper server.
   - Whisper Large V3 is great if your machine can run it, here we use the German finetune from [FloZi](https://huggingface.co/primeline/whisper-large-v3-german)
   - Alternatively you can also use [whisper.cpp](https://github.com/ggerganov/whisper.cpp) 
   - Ensure that the IP and port are correctly set if you are using a diffenret model / server
2. **Local LLM Server**: Set up a server like [LMStudio](https://lmstudio.ai/), [ollama](https://ollama.com) etc.
   - In this setup, ollama is used.
3. **Local TTS Server**: We use [Coqui xTTS-v2](https://huggingface.co/coqui/XTTS-v2) (or any other TTS server which uses the same API format).
Start all servers with 'uvicorn aiy_box:app --reload' 


## Installation
1. Clone the repository.
2. Install the required Python packages - it's a good idea to have separate virtual environments for each project
3. Follow the instructions for setting up the local server (STT, LLM, TTS).
4. Update the IP addresses and ports in the `aiy_box.py` and `CALVIN_client.py` / `box_mock.py`as per your network setup.

## Usage
1. Start all the local servers (STT, LLM, TTS) with 'uvicorn aiy_box:app --reload' 
2. Run `CALVIN_client.py` on the Raspberry Pi Zero or `box_mock.py` on our local machine .
3. Wait until the button on top of the Voice Kit lights up green (or box_mock.py says "hold ctrl to record").
4. Interact with the system using voice (press the button once to start and to stop recording). Answers will always be provided by audio, and if a monitor is connected also in the terminal.
5. There are hotwords to restart the conversation ('neustart'), stopping the service ('beenden') and for adjusting the volume ('leiser/lauter'), feel free to adjust those to your needs
6. Customize the assistant's persona if needed.

## Customization
- Modify the `system_prompt` in the script to change the assistant's persona.
- Adjust the code for language, voice, and other preferences.

## Troubleshooting
- Ensure all servers are running and accessible from the Raspberry Pi.
- Check network settings and IP configurations, try to reach the servers directly form the Pi's terminal.
- Verify the audio hardware of the Raspberry Pi Zero is functioning correctly.

## Thanks & Contributions
- Many thanks to the open source community for providing these awesome tools and building blocks!
- Feel free to fork the project and contribute to its development. Any enhancements, especially in optimization for Raspberry Pi Zero, are welcome.

## License
- This project is open-source and available under MIT.
