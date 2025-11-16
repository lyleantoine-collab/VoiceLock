# modules/voicelock.py — Universal Voice Biometric Gate
# MIT License | lyleantoine-collab | v0.2
# Full overwrite — safe, clean, ready for AI integration

import sounddevice as sd
import numpy as np
import json
import os
import yaml
from datetime import datetime
from resemblyzer import VoiceEncoder, preprocess_wav

# === LOAD CONFIG ===
try:
    with open("config.yaml", "r") as f:
        CONFIG = yaml.safe_load(f)
except FileNotFoundError:
    print("config.yaml not found. Using defaults.")
    CONFIG = {}

# === DEFAULTS (from config or fallback) ===
DB = "voicelock_db.json"
DUR = CONFIG.get("duration", 3.0)
SR = CONFIG.get("sample_rate", 16000)
THRESH = CONFIG.get("threshold", 0.8)
REQ_PHRASE = CONFIG.get("require_phrase", False)
PHRASE = CONFIG.get("phrase", "lyle authorize")
DEFAULT_USER = CONFIG.get("default_user", "lyle")

# === ENCODER ===
encoder = VoiceEncoder()

# === RECORD & PREPROCESS ===
def _record():
    print(f"Speak now ({DUR}s)...")
    audio = sd.rec(int(DUR * SR), samplerate=SR, channels=1, dtype='float32')
    sd.wait()
    return preprocess_wav(audio.flatten())

# === ENROLL USER ===
def enroll(user_id=DEFAULT_USER):
    wav = _record()
    embed = encoder.embed_utterance(wav)
    db = {} if not os.path.exists(DB) else json.load(open(DB))
    db[user_id] = embed.tolist()
    json.dump(db, open(DB, 'w'), indent=2)
    print(f"ENROLLED: {user_id}")

# === VERIFY USER ===
def verify(wav, user_id=DEFAULT_USER):
    if not os.path.exists(DB):
        return False
    db = json.load(open(DB))
    if user_id not in db:
        return False
    saved = np.array(db[user_id])
    current = encoder.embed_utterance(wav)
    sim = np.dot(saved, current) / (np.linalg.norm(saved) * np.linalg.norm(current))
    return sim > THRESH

# === GATE DECORATOR ===
def gate(user_id=None):
    user_id = user_id or DEFAULT_USER
    def decorator(func):
        def wrapper(*args, **kwargs):
            wav = _record()
            if REQ_PHRASE:
                said = input(f"Say: '{PHRASE}': ").strip().lower()
                if said != PHRASE.lower():
                    print("PHRASE DENIED")
                    return None
            if verify(wav, user_id):
                print(f"[{_now()}] ACCESS GRANTED: {user_id}")
                return func(*args, **kwargs)
            print(f"[{_now()}] ACCESS DENIED")
            return None
        return wrapper
    return decorator

# === MULTI-USER TOOLS ===
def list_users():
    if not os.path.exists(DB):
        print("No users enrolled.")
        return []
    db = json.load(open(DB))
    users = list(db.keys())
    print(f"Users: {', '.join(users)}")
    return users

def delete_user(user_id):
    if not os.path.exists(DB):
        print("No DB.")
        return
    db = json.load(open(DB))
    if user_id in db:
        del db[user_id]
        json.dump(db, open(DB, 'w'), indent=2)
        print(f"DELETED: {user_id}")
    else:
        print("User not found.")

# === INTERNAL ===
def _now():
    return datetime.now().strftime("%H:%M:%S")
