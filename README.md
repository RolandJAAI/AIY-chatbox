# ChatBox - A Local Implementation of Google AIY Voice Kit

## Overview
ChatBox is a custom implementation of [Google AIY Voice Kit](https://aiyprojects.withgoogle.com/voice/). It utilizes local Speech-To-Text (STT), local Large Language Model (LLM), and local Text-To-Speech (TTS) services, all running on a MacBook within the same network. This setup is designed to work with the Google AIY Voice Kit which contains a Raspberry Pi Zero, speaker, and microphone, and the current system prompt establishes a tutor for a personalized learning assistant experience, specifically tailored for children aged 10-13 years.


![ChatBox using Google AIY Voice Kit](https://github.com/RolandJAAI/chatbox/blob/main/chatbox.jpeg)

## Features
- **Local STT**: Converts speech to text using a local Whisper server.
- **Local LLM**: Processes and understands queries using an LLMStudio API (or any OpenAI style API).
- **Local TTS**: Converts text responses back into speech using Coqui TTS.
- **Interactive LED Indicators**: Provides visual feedback during different operations.
- **Customizable Assistant Persona**: Set up your assistant persona, "Teacher Thorsten" by default, with a specific interaction style.

## Prerequisites
- Google AIY Voice Kit with Raspberry Pi Zero, speaker, microphone led-button.
- MacBook (Tested on M1 64GB MAX) or any other local machine which can run the STT, LLM, and TTS services.
- Python 3 and necessary libraries (as per the provided script).

## Server Requirements
1. **Local STT Server**: Run a local Whisper server.
   - Use the provided code snippet for setting up the server (adapted from the example on the [Huggingface docs](https://huggingface.co/docs/transformers/pipeline_webserver)).
   - Alternatively you can also use [whisper.cpp](https://github.com/ggerganov/whisper.cpp) which is even faster, but I struggled a bit with the quality for German STT
   - Ensure that the IP and port are correctly set in the `chatbox_local_text.py` file.
2. **Local LLM Server**: Set up a server like [LMStudio](https://lmstudio.ai/), ollama etc.
   - In this setup, LMStudio with `em-german leo mistral 7b Q5` is used.
   - Ensure that the IP and port are correctly set in the `chatbox_local_text.py` file.
3. **Local TTS Server**: Use [Coqui TTS](https://github.com/coqui-ai/TTS) and their included TTS server (or any other TTS server which uses the same API format).
   - Startup command: `tts-server --model_name tts_models/de/thorsten/tacotron2-DDC`.
   - Ensure that the IP and port are correctly set in the `chatbox_local_text.py` file.

## Installation
1. Clone the repository.
2. Install the required Python packages. (note to myself: venvs are called hf-whisper for STT and TTS for, well, TTS).
3. Follow the instructions for setting up the local servers (STT, LLM, TTS).
4. Update the IP addresses and ports in the `chatbox_local_text.py` as per your network setup.

## Usage
1. Start all the local servers (STT, LLM, TTS).
2. Run `chatbox_local_text.py` on the Raspberry Pi Zero.
3. Wait until the button on top of the Voice Kit lights up green.
4. Interact with the system using voice (press the button to start/stop recording) or by typing in the terminal.
5. There are hotwords to restart the conversation ('neustart'), stopping the service ('beenden') and for adjusting the volume ('leiser/lauter'), feel free to adjust those to your needs in '`chatbox_local_text.py`
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
