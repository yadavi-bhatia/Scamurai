from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import threading
import time

from app.main import run_pipeline

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

latest_result = {}

def simulate_call():
    global latest_result

    with open("audio1.wav", "rb") as f:
        audio_bytes = f.read()

    while True:
        result = run_pipeline(audio_bytes)
        latest_result = result
        time.sleep(2)


@app.get("/start-call")
def start_call():
    thread = threading.Thread(target=simulate_call)
    thread.start()
    return {"status": "started"}


@app.get("/get-result")
def get_result():
    return latest_result