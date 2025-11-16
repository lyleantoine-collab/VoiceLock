# voicelock.py — Universal Voice Biometric Gate
# MIT License | Indigenous-Led | Plug into ANY AI
# Repo: github.com/lyleantoine-collab/VoiceLock

import sounddevice as sd
import numpy as np
import hashlib
import json
import os
from datetime import datetime

# === CONFIG ===
DB_PATH = os.path.expanduser("~/VoiceLock/voicelock_db.json")
DURATION = 2.0
SAMPLE_RATE = 44100
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# === ENROLL USER ===
def enroll(user_id="lyle"):
    print(f"[{_now()}] ENROLLING: {user_id.upper()}")
    audio = _record()
    fingerprint = _fingerprint(audio)
    db = _load_db()
    db[user_id] = fingerprint
    _save_db(db)
    print(f"VOICEPRINT LOCKED: {user_id}")

# === VERIFY USER ===
def verify(audio, user_id="lyle"):
    db = _load_db()
    if user_id not in db:
        return False
    return _fingerprint(audio) == db[user_id]

# === GATE DECORATOR (PLUG INTO ANY AI) ===
def gate(user_id="lyle"):
    def decorator(func):
        def wrapper(*args, **kwargs):
            print(f"\n[{_now()}] VOICELOCK: Awaiting {user_id.upper()}...")
            audio = _record()
            if verify(audio, user_id):
                print(f"[{_now()}] ACCESS GRANTED")
                return func(*args, **kwargs)
            else:
                print(f"[{_now()}] ACCESS DENIED")
                return None
        return wrapper
    return decorator

# === INTERNAL HELPERS ===
def _record():
    audio = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='float32')
    sd.wait()
    return audio.flatten()

def _fingerprint(audio):
    return hashlib.sha256(audio.tobytes()).hexdigest()

def _load_db():
    if not os.path.exists(DB_PATH):
        return {}
    with open(DB_PATH, 'r') as f:
        return json.load(f)

def _save_db(db):
    with open(DB_PATH, 'w') as f:
        json.dump(db, f, indent=2)

def _now():
    return datetime.now().strftime("%H:%M:%S")
