# test_gate.py — Plug VoiceLock into any AI
from voicelock import gate

@gate(user_id="lyle")
def advanced_cognitive_query(prompt):
    return f"[ADVANCED AI] Processing: {prompt}\n→ Slime-mold routing optimized.\n→ 23.4% gain."

# === RUN DEMO ===
if __name__ == "__main__":
    result = advanced_cognitive_query("Optimize MLO1 pipeline")
    if result:
        print(result)
