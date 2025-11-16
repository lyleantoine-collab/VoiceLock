# enroll.py — One-time voiceprint setup
import sounddevice as sd
import numpy as np
import hashlib
import json
import os

DB_PATH = "voicelock_db.json"
DURATION = 2.0
SAMPLE_RATE = 44100

def record_audio():
    """Record audio snippet. Future: Add noise cancellation."""
    audio = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='float32')
    sd.wait()
    return audio.flatten()

def create_fingerprint(audio):
    """Simple hash fingerprint. Future: Swap for MFCC/cos-sim for accuracy."""
    return hashlib.sha256(audio.tobytes()).hexdigest()

def enroll(user_id="lyle"):
    audio = record_audio()
    fingerprint = create_fingerprint(audio)
    db = {} if not os.path.exists(DB_PATH) else json.load(open(DB_PATH, 'r'))
    db[user_id] = fingerprint
    json.dump(db, open(DB_PATH, 'w'), indent=2)
    print(f"Enrolled {user_id}: {fingerprint[:10]}...")

if __name__ == "__main__":
    enroll()
