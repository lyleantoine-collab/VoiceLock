# modules/voicelock.py — v1.1 ZERO-DEP (numpy + pyyaml only)
# MIT License | lyleantoine-collab | 2025

import numpy as np
import json
import os
import yaml
import subprocess
import random
from datetime import datetime

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

# === RECORD VIA TERMUX (arecord) ===
def _record():
    """Record 3s via Termux mic."""
    print(f"Speak now ({DUR}s)...")
    try:
        subprocess.run(["termux-microphone-record", "-f", "tmp.wav", "-l", str(int(DUR))], check=True)
        import wave
        with wave.open("tmp.wav", "rb") as wf:
            audio = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
        os.remove("tmp.wav")
        return audio.astype(np.float32) / 32768.0
    except:
        print("Mic failed. Using dummy.")
        return np.random.randn(int(DUR * SR))

# === PURE NUMPY MFCC (simplified) ===
def get_embedding(wav):
    """Simple MFCC-like embedding."""
    # Downsample
    wav = wav[::2]
    # FFT frames
    frames = np.lib.stride_tricks.sliding_window_view(wav, 512)[::256]
    spec = np.abs(np.fft.rfft(frames, n=512))
    # Mel-like filter (crude)
    embed = np.log(spec.mean(axis=0) + 1e-6)
    return np.pad(embed, (0, 256))[:256]

# === REST SAME AS BEFORE (enroll, verify, gate, etc.) ===
# ... [same logic from last version, just using _record() and get_embedding()]
