from typing import Dict
from io import BytesIO
from zipfile import ZipFile
import tempfile
import os

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from core import DanielVoice, Speech, BulkSpeech
import bson

# import zlib

app = FastAPI()


@app.get("/")
def index():
    return "Welcome to the daniel uk tts API"


def stream_files(*files):
    buffer = BytesIO()
    media_type = None

    if len(files) > 1:
        media_type = "application/octet-stream"
        contents = []

        for audio_file in files:
            with open(audio_file, 'rb') as f:
                contents.append(f.read())
                os.remove(audio_file)
        
        print(contents)

        buffer.write(bson.dumps({'data': contents}))
        buffer.seek(0)
    else:
        file = files[0]
        media_type = "audio/mpeg"
        with open(file, "rb") as f:
            buffer.write(f.read())
            buffer.seek(0)
        os.remove(file)

    return StreamingResponse(buffer, media_type=media_type)


@app.post("/generate_speech")
def generate_speech(request: Speech):
    tempfile_name = tempfile.mktemp(suffix=".mp3")

    engine = DanielVoice(request.speed)
    engine.save_to_file(request.text, tempfile_name)
    engine.await_synthesis()

    return stream_files(tempfile_name)


@app.post("/generate_speech/bulk")
def bulk_generate_speech(request: BulkSpeech):
    engine = DanielVoice(request.speed)

    tempfiles = []

    for text in request.text:
        tempfile_name = tempfile.mktemp(suffix=".mp3")
        tempfiles.append(tempfile_name)
        engine.save_to_file(text, tempfile_name)

    engine.await_synthesis()

    return stream_files(*tempfiles)