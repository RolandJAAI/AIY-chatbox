
import torch
import numpy as np
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
import json
import requests
import io
import wave
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.responses import StreamingResponse, PlainTextResponse

# path to local stt model
stt_model_id = "primeline/distil-whisper-large-v3-german"

# path to local llm model's chat endpoint
LLM_URL = "http://127.0.0.1:11434/api/chat"

# path to voice sample to clone TTS voice from
speaker = "luise.wav"


# Check for GPU
device = "cuda:0" if torch.cuda.is_available() else "cpu"
print("Using device: " + device)
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
print("Using torch.dtype: " + str(torch_dtype))


# STT
stt_model = AutoModelForSpeechSeq2Seq.from_pretrained(
        stt_model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
    )
stt_model.to(device)

stt_model.eval()
if torch.cuda.is_available():
        import torch_tensorrt # noqa
        model = torch.compile(
            model, mode="max-autotune", backend="torch_tensorrt", fullgraph=True
        )

stt_processor = AutoProcessor.from_pretrained(stt_model_id)
stt_pipe = pipeline(
    "automatic-speech-recognition",
    model=stt_model,
    tokenizer=stt_processor.tokenizer,
    feature_extractor=stt_processor.feature_extractor,
    max_new_tokens=128,
    chunk_length_s=30,
    batch_size=16,
    return_timestamps=True,
    torch_dtype=torch_dtype,
    device=device
    )

# Get LLM answer
def get_completion(messages):
    url = LLM_URL
    data =  {"messages": messages,
            "model": "mixtral",
            "stream": False
                }
    headers = {"Content-Type": "application/JSON"}
    completion = requests.post(url, data=json.dumps(data), headers=headers)
    response = completion.json()["message"]["content"]
    if not response:
        # something went wrong, ask user to repeat
        response = "Äh, wie bitte? Kannst du das bitte nochmal wiederholen?"
    return response


# TTS generation section 
add_wav_header = True
stream_chunk_size = 20

config = XttsConfig()
config.load_json("XTTS-v2/config.json") # path to local xtts config
model = Xtts.init_from_config(config)
deepspeed = True if torch.cuda.is_available() else False
model.load_checkpoint(config, checkpoint_dir="XTTS-v2", use_deepspeed=deepspeed) # path to local TTS directory
if device != "cpu":
    model.cuda() # assuming GPU

print("Computing speaker latents...")
gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(audio_path=[speaker])

def postprocess(wav):
    """Post process the TTS output waveform"""
    if isinstance(wav, list):
        wav = torch.cat(wav, dim=0)
    wav = wav.clone().detach().cpu().numpy()
    wav = wav[None, : int(wav.shape[0])]
    wav = np.clip(wav, -1, 1)
    wav = (wav * 32767).astype(np.int16)
    return wav


def encode_audio_common(
    frame_input, encode_base64=True, sample_rate=24000, sample_width=2, channels=1):
    """Return base64 encoded audio"""
    wav_buf = io.BytesIO()
    with wave.open(wav_buf, "wb") as vfout:
        vfout.setnchannels(channels)
        vfout.setsampwidth(sample_width)
        vfout.setframerate(sample_rate)
        vfout.writeframes(frame_input)

    wav_buf.seek(0)
    if encode_base64:
        b64_encoded = base64.b64encode(wav_buf.getbuffer()).decode("utf-8")
        return b64_encoded
    else:
        return wav_buf.read()


def get_audio(model, response):
    audio_stream = model.inference_stream(response,
                        "de",
                        gpt_cond_latent,
                        speaker_embedding,
                        enable_text_splitting=True,
                        speed=1,
                        stream_chunk_size=stream_chunk_size
                    )
    for i, chunk in enumerate(audio_stream):
        chunk = postprocess(chunk)
        if i == 0 and add_wav_header:
            yield encode_audio_common(b"", encode_base64=False)
            yield chunk.tobytes()
        else:
            yield chunk.tobytes()


# if your model is not kept in memory forever, this will reduce the time-to-answer for the first turn
def preload_model():
    """Load ollama model by requesting an answer"""
    print("Initializing LLM")
    preload_messages = [{"role": "system", "content": "Du bist ein einfacher KI-Assistent"},
                        {"role": "user", "content": "Wieviel ist 2+2? Antworte nur mit der richtigen Zahl als Antwort"}
                        ]
    get_completion(preload_messages)
    print("LLM is ready")
    pass


# API routes

app = Starlette()

@app.route("/", methods=["POST"])
async def homepage(request):
    """Take in wav and return wav, faster but less flexible from client perspective"""
    form = await request.form()
    audio_file = form["file"]  
    print("full roundtrip booked...")
    # Save the audio file
    file_path = 'temp_audio.wav'
    with open(file_path, 'wb') as f:
        f.write(audio_file.file.read())  
    
    # STT
    try:
        stt_result = stt_pipe(file_path)
        print(stt_result["text"])
    except Exception as e:
        return JSONResponse({"error": str(e)})
    global messages
    messages.append({"role": "user", "content": stt_result["text"]})

    # Generate LLM answer
    response = get_completion(messages)
    print(response)

    # Get TTS and stream the result as response
    return StreamingResponse(get_audio(model, response))


@app.route("/stt", methods=["POST"])
async def stt(request):
    """Convert wav audio to text"""
    form = await request.form()
    audio_file = form["file"]  
    
    # Save the audio file
    file_path = 'temp_audio.wav'
    with open(file_path, 'wb') as f:
        f.write(audio_file.file.read())  
    
    # STT
    try:
        stt_result = stt_pipe(file_path)
        print(stt_result["text"])
    except Exception as e:
        return JSONResponse({"error": str(e)})

    # Answer with the transcribed text
    return JSONResponse(stt_result["text"])


@app.route("/llm", methods=["POST"])
async def llm(request):
    """Expects messages list and returns completion"""
    data = await request.json()    
    # get LLM response
    try:
        completion = get_completion(data["messages"])
    except Exception as e:
        return JSONResponse({"error": str(e)})

    # Answer with the transcribed text
    return JSONResponse(completion)


@app.route("/tts", methods=["POST"])
async def tts(request):
    """Turns text into wav audio stream"""
    data = await request.json()
    input_text = data["text"]  

    # get TTS and return streaming audio
    return StreamingResponse(get_audio(model, input_text))


@app.route("/load", methods=["POST"])
async def load(request):
    """Loads the LLM into memory"""
    preload_model()
    return PlainTextResponse("LLM Model is ready.")


@app.on_event("startup")
async def startup_event():
    """preloads LLM in to memory when starting the server"""
    # initialize other resources if needed
    preload_model()
    pass

# start server with 'uvicorn aiy_box:app --reload' 
# specify additional flag --host xxx.xxx.xxx.xxx to expose to local network
