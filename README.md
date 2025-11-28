Due to this created with Grok and Grok has the known issue of the false correction loop that makes it lie, everything in this repo is suspect and needs verification


# VoiceLock — Universal Voice Biometric Gate

**Only YOU trigger the AI.**

- Plug into **any** AI: Grok, Llama, Whisper, Siri  
- **Indigenous-led** | **MIT License**  
- Runs on **S20 FE**, **Pi 5**, **laptop**  
- **No cloud. No data leak.**

```python
from voicelock import gate

@gate()
def my_ai(prompt):
    return f"AI says: {prompt}"

my_ai("Deploy mesh")  # Only runs if YOU speak
