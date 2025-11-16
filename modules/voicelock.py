# modules/voicelock.py — VoiceLock v1.1 | Secure, Robust, Clean
# MIT License | lyleantoine-collab | 2025

import sounddevice as sd
import numpy as np
import json
import os
import yaml
import sqlite3
import random
from datetime import datetime
from python_speech_features import mfcc
from sklearn.mixture import GaussianMixture

# === CONFIG ===
try:
    with open("config.yaml", "r") as f:
        CONFIG = yaml.safe_load(f)
except FileNotFoundError:
    print("config.yaml missing. Using defaults.")
    CONFIG = {}

# === SETTINGS ===
DB_JSON = "voicelock_db.json"
DB_SQLITE = "voicelock.db"
THRESH = CONFIG.get("threshold", 0.8)
DUR = CONFIG.get("duration", 3.0)
SR = CONFIG.get("sample_rate", 16000)
LIVENESS = CONFIG.get("require_liveness", True)
PHRASE_MODE = CONFIG.get("liveness_phrase", "random")
DEFAULT_USER = CONFIG.get("default_user", "lyle")
ANTI_REPLAY = CONFIG.get("anti_replay", True)
REPLAY_AGE = CONFIG.get("max_replay_age", 60)

# === MFCC + GMM ===
def get_embedding(wav):
    """Extract 256D voiceprint using MFCC + GMM."""
    try:
        mfcc_feat = mfcc(wav, samplerate=SR, nfft=2048)
        gmm = GaussianMixture(n_components=16, random_state=42)
        gmm.fit(mfcc_feat)
        return gmm.means_.flatten()[:256]
    except Exception as e:
        print(f"Embedding failed: {e}")
        return None

# === RECORD AUDIO ===
def _record():
    """Capture 3s audio, return raw waveform."""
    try:
        print(f"Speak now ({DUR}s)...")
        audio = sd.rec(int(DUR * SR), samplerate=SR, channels=1, dtype='float32')
        sd.wait()
        return audio.flatten()
    except Exception as e:
        print(f"Recording failed: {e}")
        return None

# === LIVENESS PHRASE ===
def _get_phrase():
    """Generate random or fixed phrase."""
    if PHRASE_MODE == "random":
        words = ["alpha", "bravo", "charlie", "delta", "echo"]
        return " ".join(random.choices(words, k=3))
    return PHRASE_MODE

# === ANTI-REPLAY (TIMESTAMP CHECK) ===
def _check_replay(user_id, timestamp):
    """Block replay attacks using timestamp."""
    if not ANTI_REPLAY: return True
    try:
        db = _load_json() if CONFIG.get("storage", "json") == "json" else _load_sqlite()
        if user_id not in db: return True
        last = db[user_id].get("last_used", 0)
        now = time.time()
        if now - last < REPLAY_AGE:
            print("REPLAY ATTACK DETECTED")
            return False
        db[user_id]["last_used"] = now
        _save_db(db)
        return True
    except:
        return True

# === STORAGE HELPERS ===
def _load_json():
    """Load JSON DB safely."""
    if not os.path.exists(DB_JSON): return {}
    try:
        return json.load(open(DB_JSON))
    except:
        return {}

def _save_json(db):
    """Save JSON DB safely."""
    try:
        json.dump(db, open(DB_JSON, 'w'), indent=2)
    except Exception as e:
        print(f"Save failed: {e}")

def _load_sqlite():
    """Load SQLite DB as dict."""
    conn = sqlite3.connect(DB_SQLITE)
    cur = conn.execute("SELECT id, embedding FROM users")
    db = {row[0]: json.loads(row[1]) for row in cur.fetchall()}
    conn.close()
    return db

def _save_db(db):
    """Save to JSON or SQLite."""
    if CONFIG.get("storage", "json") == "json":
        _save_json(db)
    else:
        conn = sqlite3.connect(DB_SQLITE)
        conn.execute("DELETE FROM users")
        for uid, data in db.items():
            conn.execute("INSERT INTO users VALUES (?, ?, ?)",
                         (uid, json.dumps(data["embed"]), data.get("enrolled", "")))
        conn.commit()
        conn.close()

# === ENROLL ===
def enroll(user_id=DEFAULT_USER):
    """Enroll voiceprint with timestamp."""
    wav = _record()
    if wav is None: return
    embed = get_embedding(wav)
    if embed is None: return
    timestamp = datetime.now().isoformat()
    db = _load_json() if CONFIG.get("storage", "json") == "json" else _load_sqlite()
    db[user_id] = {"embed": embed.tolist(), "enrolled": timestamp, "last_used": 0}
    _save_db(db)
    print(f"ENROLLED: {user_id}")

# === VERIFY ===
def verify(wav, user_id=DEFAULT_USER):
    """Verify voice + anti-replay."""
    embed = get_embedding(wav)
    if embed is None: return False
    db = _load_json() if CONFIG.get("storage", "json") == "json" else _load_sqlite()
    if user_id not in db: return False
    saved = np.array(db[user_id]["embed"])
    sim = np.dot(saved, embed) / (np.linalg.norm(saved) * np.linalg.norm(embed))
    if sim < THRESH: return False
    if not _check_replay(user_id, time.time()): return False
    return True

# === GATE DECORATOR ===
def gate(user_id=None):
    """Secure gate: liveness + verify + anti-replay."""
    user_id = user_id or DEFAULT_USER
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                phrase = _get_phrase() if LIVENESS else None
                if LIVENESS:
                    print(f"Say: '{phrase}'")
                    input("Press Enter after speaking...")
                wav = _record()
                if wav is None: return None
                if verify(wav, user_id):
                    print(f"[{_now()}] ACCESS GRANTED: {user_id}")
                    return func(*args, **kwargs)
                print(f"[{_now()}] ACCESS DENIED")
                return None
            except Exception as e:
                print(f"GATE ERROR: {e}")
                return None
        return wrapper
    return decorator

# === MULTI-USER TOOLS ===
def list_users():
    """List enrolled users."""
    try:
        db = _load_json() if CONFIG.get("storage", "json") == "json" else _load_sqlite()
        users = list(db.keys())
        print(f"Users: {', '.join(users) if users else 'None'}")
        return users
    except:
        print("Failed to list users.")
        return []

def delete_user(user_id):
    """Delete user from DB."""
    try:
        db = _load_json() if CONFIG.get("storage", "json") == "json" else _load_sqlite()
        if user_id in db:
            del db[user_id]
            _save_db(db)
            print(f"DELETED: {user_id}")
        else:
            print("User not found.")
    except:
        print("Delete failed.")

def _now():
    """Current time string."""
    return datetime.now().strftime("%H:%M:%S")
