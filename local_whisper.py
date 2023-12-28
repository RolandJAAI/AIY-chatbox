from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
import asyncio
import soundfile as sf
from io import BytesIO
from transformers import pipeline
import os

local_model = 'whisper-large-v3-german'

app = Starlette()


@app.route("/", methods=["POST"])
async def homepage(request):
    form = await request.form()
    audio_file = form["file"]  

    # Save the audio file
    file_path = 'temp_audio.wav'
    with open(file_path, 'wb') as f:
        f.write(audio_file.file.read())  

    # Now read the saved audio file
    array, sampling_rate = sf.read(file_path)

    # STT using local whisper model which needs to be hf format and in the defined folder
    generator = pipeline("automatic-speech-recognition", model=local_model)
    try:
        result = generator(array)
        print(result)
    except Exception as e:
        return JSONResponse({"error": str(e)})

    return JSONResponse(result)


@app.on_event("startup")
async def startup_event():
    # initialize other resources if needed
    pass

# start server with `uvicorn local_whisper:app --reload`
