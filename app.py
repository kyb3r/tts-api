from typing import Dict
from io import BytesIO
import tempfile
from pathlib import Path
import os, signal
import zlib

import threading

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from core import DanielVoice, Speech, BulkSpeech
import bson
import psutil
import asyncio

# import zlib


app = FastAPI()

@app.on_event("startup")
async def on_startup():
    global engine
    global lock

    engine = DanielVoice(speed=180)
    lock = threading.Lock()
    asyncio.create_task(speech_process_killer_loop())

    print("INFO:     Initialised tts engine")


async def speech_process_killer_loop():
    '''Try to kill speech process every 5 mins
    because for some reason with prolonged used, 
    the output files from the tts process are empty
    '''
    while True:
        print('Killing speech process')
        restart_speech_process()
        await asyncio.sleep(60)


def restart_speech_process():
    with lock:
        matches = [
            p.info["pid"]
            for p in psutil.process_iter(attrs=["pid", "name"])
            if p.info["name"] and "com.apple.speech.speechsynthesisd" in p.info["name"]
        ]
        if not matches:
            return
        else:
            os.kill(matches[0], signal.SIGKILL)


@app.on_event("shutdown")
async def on_shutdown():
    engine.stop()

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    response = await call_next(request)
    restart_speech_process()
    return response

class SpeechProcessDeadError:  # sometimes the nsss speech process dies and just creates empty files
    pass


def stream_files(*files):
    buffer = BytesIO()
    media_type = "application/octet-stream"

    files = sorted(
        files, key=lambda f: int(os.path.basename(f))
    )  # sort by making filenames integers
    
    contents = []

    for audio_file in files:
        with open(audio_file, "rb") as f:
            contents.append(f.read())
        os.remove(audio_file)

    length = len(contents)
    empty = sum(1 for x in contents if not x)
    if empty/length > 0.1:
        return SpeechProcessDeadError

    data = zlib.compress(bson.encode({"data": contents}))
    headers = {'content-length': str(len(data))}
    buffer.write(data)
    buffer.seek(0)

    return StreamingResponse(buffer, media_type=media_type, headers=headers)


import functools

def retry(num=5):
    def decorator(func):
        @functools.wraps(func)
        def new_func(*args, **kwargs):
            for _ in range(num):
                ret = func(*args, **kwargs)
                if ret != SpeechProcessDeadError:
                    return ret
                else:
                    print("\n\n\n\n\nRESTARTING SPEECH PROCESS", end="-----------\n\n\n\n\n")
                    restart_speech_process()
                    with lock:
                        engine.stop()
                        engine.init()

        return new_func

    return decorator

@app.get("/")
def index():
    return "Welcome to the daniel uk tts API"

@app.post("/generate_speech")
@retry(5)
def generate_speech(request: Speech):
    tempfile_name = tempfile.mktemp(suffix=".mp3")

    with lock:
        engine.save_to_file(request.text, tempfile_name)
        engine.await_synthesis()

    return stream_files(tempfile_name)

@app.post("/generate_speech/bulk")
@retry(5)
def bulk_generate_speech(request: BulkSpeech):

    tempdir = tempfile.mkdtemp()
    tempfiles = []

    lock.acquire()

    for index, text in enumerate(request.text):
        tf = Path(tempdir) / str(index)
        engine.save_to_file(text, tf)
        tempfiles.append(tf)

    print(f"Generating in bulk for {len(tempfiles)} files")
    engine.await_synthesis()

    lock.release()

    return stream_files(*tempfiles)
