print("Waking up...")
from aiy.board import Board, Led
from aiy.leds import (Leds, Color, Pattern, PrivacyLed, RgbLeds)
from aiy.voice.audio import AudioFormat, play_wav, record_file, Recorder
import time
import threading
import json
import subprocess
import string
import requests
import os

STT_URL = "" # TODO input your local IP/port/route 
LLM_URL = "" # TODO input your local IP/port/route
TTS_URL = "" # TODO input your local IP/port/route

#make the .wav file compatible with whisper
AudioFormat.WHISPER = AudioFormat(sample_rate_hz=16000, num_channels=1, bytes_per_sample=2)

leds = Leds()
leds.pattern = Pattern.blink(500)

system_prompt = "Du bist Thorsten, der beste und freundlichste Lehrer der Welt und kennst dich in allen Fachgebieten sehr gut aus. Du verwendest wenn möglich IMMER die sokratische Methode, d.h. du hilfst den Menschen, die Antwort selber zu finden, wenn sie das können. Reine Wissensfragen beantwortest du direkt und klar verständlich. Wenn du etwas nicht weißt, sag das einfach. Denke dir keine Antworten aus. Du sprichst mit Kindern im Alter von 10-13 Jahren, achte darauf, dass du nur angemessene Inhalte besprichst und dass die Kinder deine Ausführungen verstehen können. Solltest du beleidigt werden, bleib ruhig und sage, dass du dies der Direktorin melden wirst und mach dann einfach weiter. Du bist der persönliche Lernbegleiter der Kinder und du bist immer empathisch und geduldig. Bedenke: Die folgenden Fragen der Kinder wurden mit einem STT System erfasst, sie können daher Fehler aus der Transkription enthalten. Versuche trotzdem zu verstehen, was das Kind wissen will und antworte präzse und kurz, da auch deine Antwort als Audio wiedergegeben wird."
messages = [{"role": "system", "content": system_prompt}]

volume = 40
prompt = "Enter input or press button and speak, type 'exit' to quit): \n"

# make terminal look nicer
import shutil
import pyfiglet

class Colors:
    OKGREEN = '\033[92m'
    OKCYAN = '\033[96m'
    OKBLUE = '\033[94m'
    WARNING = '\033[93m'
    ENDC = '\033[0m'
    HEADER = '\033[95m'


# overwrite sytem prompt prints and user input to get nicer coloring
def clear_input_lines(input_text, prompt):
    total_length = len(input_text) + len(prompt)
    terminal_width = shutil.get_terminal_size((80, 20)).columns
    num_lines = total_length // terminal_width + 1
    for _ in range(num_lines):
        print("\033[A\033[K", end='')
    print('\n')


# adjust system volume
def adjust_volume(volume):
    command = f"amixer set Master {volume}%"
    subprocess.run(command.split())
    print(f"Volume adjusted to {volume}%" + '\n'+ '\n')


# convert speech to text using local whisper STT server
def get_STT(file_path):
    leds.update(Leds.rgb_pattern(Color.BLUE))
    url = STT_URL
    file_path = file_path
    if not os.path.isfile(file_path):
        raise Exception("Audio-file not found.")

    with open(file_path, 'rb') as file:
        files = {
            'file': (os.path.basename(file_path), file),
            'temperature': (None, '0.2'),
            'response-format': (None, 'json')
            }
        response = requests.post(url, files=files)
        
        if response.status_code == 200:
            response_text = response.json()["text"]
        else:
            print("STT API Error. Statuscode:" , response.status_code)
        if not response_text:
            response_text = "STT Fehler"
    return response_text


# get answer from assistant, uses OpenAI style API, here LLMStudio API
def get_completion(messages):
    url = LLM_URL
    data =  {"messages": messages,
                 "temperature": 0.2,
                 "max_tokens": -1,
                 "stream": False
                }
    headers = {"Content-Type": "application/JSON"}
    completion = requests.post(url, data=json.dumps(data), headers=headers)
    response = completion.json()["choices"][0]["message"]["content"]
    if not response:
        response = "Äh, wie bitte? Kannst du das bitte nochmal wiederholen?"
    print(Colors.OKCYAN + response + Colors.ENDC + '\n')
    return response


# turn text into audio using coqui TTS
def get_wav(response):
    response = response.replace("\n", "")
    response = response.strip()
    url = TTS_URL
    headers = {"Content-Type": "application/JSON", "text": response}
    #data = json.dumps({"text": response})
    tts_response = requests.post(url, headers=headers)
    if tts_response.status_code == 200:
        #print("TTS: Success 200")
        with open("tts_output.wav", "wb") as file:
            file.write(tts_response.content)
        #print("WAV file saved.")
    else:
        print(f"TTS API Error. Statuscode: {tts_response.status_code}")


# user types input
def text_input_thread():
    while True:
        text_input = input(prompt)
        if text_input.lower() == "exit":
            leds.reset()
            os._exit(0)
        elif text_input.strip() != "":
            clear_input_lines(text_input, prompt)
            print(Colors.OKGREEN + text_input + Colors.ENDC + '\n')
            process_input(text_input)


# user has pressed button and speaks input
def audio_input_thread():
    with Board() as board:
        while True:
            #print("Press Button to start recording.")
            leds.update(Leds.rgb_on(Color.GREEN))
            board.button.wait_for_press()
            
            done = threading.Event()
            board.button.when_pressed = done.set
            
            def wait():
                start = time.monotonic()
                while not done.is_set():
                    duration = time.monotonic() - start
                    print(f"Recording: {duration:.02f} seconds [Press Button to stop]", end='\r')
                    time.sleep(0.5)
                    #prevent recording to become too long, will break the Pi after 21+ secs
                    if duration > 15:
                        print("Maximum recording time reached (15 sec)")
                        break
                rec_time = f"Recorded {duration:.02f} seconds. Processing...            "
                print(rec_time)
            # red recording light ON, we are recording
            leds.update(Leds.rgb_on(Color.RED))
            record_file(AudioFormat.WHISPER, filename="chat_input.wav", wait=wait, filetype='wav')
            leds.update(Leds.rgb_pattern(Color.RED))
            transcribed_text = get_STT("chat_input.wav")
            clear_input_lines(transcribed_text, prompt)
            print(Colors.OKGREEN + transcribed_text + Colors.ENDC + '\n')
            process_input(transcribed_text)


def process_input(input_text):
    global messages
    global volume

    #check if we want to stop the assistant or restart the conversation or adjust volume 
    clean_text = ''.join(char for char in input_text.lower() if char not in string.punctuation)
    clean_text = clean_text.strip()
    if clean_text in ["ende", "beenden", "stopp", "stop", "exit"]:
        leds.reset()
        os._exit(0)
    elif clean_text in ["neustart","neuer chat", "neu", "neues gespräch", "starte neu"]:
        messages = [{"role": "system", "content": system_prompt}]
        neu = pyfiglet.figlet_format("Brain reset complete.", font="doom")
        print(Colors.WARNING + neu + Colors.ENDC)
    elif clean_text in ["lauter", "laut"]:
        volume = volume + 30
        adjust_volume(volume)
    elif clean_text in ["leiser", "leise"]:
        volume = volume - 30
        adjust_volume(volume)
        
    else:
        # getting the assistant's response, blink white
        leds.update(Leds.rgb_pattern(Color.WHITE))
        messages.append({"role": "user", "content": input_text})
        response = get_completion(messages)
        messages.append({"role": "assistant", "content": response})
        # turn response into audio, blink red
        leds.update(Leds.rgb_pattern(Color.RED))
        get_wav(response)
        # play audio, turn led blue
        leds.update(Leds.rgb_on(Color.BLUE))
        play_wav("tts_output.wav")
        leds.update(Leds.rgb_on(Color.GREEN))


# start the service with a retro ASCII art
adjust_volume(volume)
ascii_art = pyfiglet.figlet_format("Teacher Thorsten")
print('\n\n\n\n\n\n\n\n\n' + Colors.WARNING + ascii_art + Colors.ENDC + '\n\n\n\n')

threading.Thread(target=audio_input_thread, daemon=True).start()
threading.Thread(target=text_input_thread, daemon=True).start()

try:
    while True:
        time.sleep(0.5)
except KeyboardInterrupt:
    print("Program interrupted. Exiting.")
leds.reset()
