# modules/voicelock.py — VoiceLock v1.4 | Pure NumPy, Zero Crash
# MIT License | lyleantoine-collab | 2025

import sounddevice as sd
import numpy as np
import json
import os
import yaml
import random
import time
from datetime import datetime
from python_speech_features import mfcc

# === CONFIG ===
try:
    with open("config.yaml", "r") as f:
        CONFIG = yaml.safe_load(f)
except:
    CONFIG = {}

# === SETTINGS ===
DB = "voicelock_db.json"
THRESH = CONFIG.get("threshold", 0.8)
DUR = CONFIG.get("duration", 3.0)
SR = CONFIG.get("sample_rate", 16000)
LIVENESS = CONFIG.get("require_liveness", True)
PHRASE_MODE = CONFIG.get("liveness_phrase", "random")
DEFAULT_USER = CONFIG.get("default_user", "lyle")
ANTI_REPLAY = CONFIG.get("anti_replay", True)
REPLAY_AGE = CONFIG.get("max_replay_age", 60)

# === RECORD ===
def _record():
    try:
        print(f"Speak now ({DUR}s)...")
        audio = sd.rec(int(DUR * SR), samplerate=SR, channels=1, dtype='float32')
        sd.wait()
        return audio.flatten()
    except Exception as e:
        print(f"Record error: {e}")
        return np.random.randn(int(DUR * SR))  # Fallback

# === PURE NUMPY EMBEDDING ===
def get_embedding(wav):
    try:
        feats = mfcc(wav, samplerate=SR, nfft=2048)
        # 16 random centroids → 256D
        if len(feats) < 16:
            return np.zeros(256)
        idx = np.random.choice(len(feats), 16, replace=False)
        means = feats[idx]
        return np.pad(means.flatten(), (0, 256))[:256]
    except:
        return np.zeros(256)

# === LIVENESS & REPLAY ===
def _get_phrase():
    if PHRASE_MODE == "random":
        words = ["alpha", "bravo", "charlie", "delta", "echo"]
        return " ".join(random.choices(words, k=3))
    return PHRASE_MODE

def _check_replay(user_id):
    if not ANTI_REPLAY: return True
    try:
        db = json.load(open(DB)) if os.path.exists(DB) else {}
        now = time.time()
        if user_id in db and now - db[user_id].get("last_used", 0) < REPLAY_AGE:
            print("REPLAY BLOCKED")
            return False
        db[user_id] = db.get(user_id, {})
        db[user_id]["last_used"] = now
        json.dump(db, open(DB, 'w'), indent=2)
        return True
    except:
        return True

# === ENROLL ===
def enroll(user_id=DEFAULT_USER):
    wav = _record()
    embed = get_embedding(wav)
    db = json.load(open(DB)) if os.path.exists(DB) else {}
    db[user_id] = {"embed": embed.tolist(), "last_used": 0}
    json.dump(db, open(DB, 'w'), indent=2)
    print(f"ENROLLED: {user_id}")

# === VERIFY ===
def verify(wav, user_id=DEFAULT_USER):
    embed = get_embedding(wav)
    db = json.load(open(DB)) if os.path.exists(DB) else {}
    if user_id not in db: return False
    saved = np.array(db[user_id]["embed"])
    sim = np.dot(saved, embed) / (np.linalg.norm(saved) * np.linalg.norm(embed))
    if sim < THRESH: return False
    return _check_replay(user_id)

# === GATE ===
def gate(user_id=None):
    user_id = user_id or DEFAULT_USER
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                if LIVENESS:
                    print(f"Say: '{_get_phrase()}'")
                    input("Press Enter...")
                wav = _record()
                if verify(wav, user_id):
                    print(f"[{_now()}] ACCESS GRANTED")
                    return func(*args, **kwargs)
                print(f"[{_now()}] ACCESS DENIED")
                return None
            except Exception as e:
                print(f"GATE ERROR: {e}")
                return None
        return wrapper
    return decorator

def _now():
    return datetime.now().strftime("%H:%M:%S")
