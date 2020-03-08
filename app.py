from typing import Dict
from io import BytesIO
import tempfile
from pathlib import Path
import os
import zlib

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
        files = sorted(files, key=lambda f: int(os.path.basename(f))) # sort by making filenames integers
        media_type = "application/octet-stream"
        contents = []

        for audio_file in files:
            with open(audio_file, 'rb') as f:
                contents.append(f.read())
            os.remove(audio_file)

        buffer.write(zlib.compress(bson.dumps({'data': contents})))
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

    tempdir = tempfile.mkdtemp()
    tempfiles = []

    for index, text in enumerate(request.text):
        tf = Path(tempdir) / str(index)
        engine.save_to_file(text, tf)
        tempfiles.append(tf)

    print(f'Generating in bulk for {len(tempfiles)} files')
    engine.await_synthesis()

    return stream_files(*tempfiles)
