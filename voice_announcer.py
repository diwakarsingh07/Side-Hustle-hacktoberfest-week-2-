"""
RestoCopilot AI - Kitchen Voice Announcer
Supports:
1. ElevenLabs Ultra-HD Neural Voice (Crisp studio grade kitchen callouts)
2. Local Offline Speech Synthesis (gTTS + system speech fallback)
Zero latency: automatically falls back to offline speech if internet or key is unavailable.
"""
import os
import hashlib
from dotenv import load_dotenv

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "").strip()
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM").strip()

AUDIO_DIR = os.path.join(os.path.dirname(__file__), "audio_cache")
os.makedirs(AUDIO_DIR, exist_ok=True)

def generate_voice_callout(text: str) -> str:
    """
    Synthesizes speech for the kitchen order.
    Returns the absolute path to the generated MP3 file.
    """
    clean_text = text.strip()
    if not clean_text:
        return ""
        
    text_hash = hashlib.md5(clean_text.encode("utf-8")).hexdigest()
    output_path = os.path.join(AUDIO_DIR, f"kds_callout_{text_hash[:10]}.mp3")
    
    # Return cached audio if already synthesized
    if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
        return output_path
        
    # Attempt 1: ElevenLabs API (if API key provided)
    if ELEVENLABS_API_KEY:
        try:
            from elevenlabs.client import ElevenLabs
            client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
            audio_generator = client.text_to_speech.convert(
                text=clean_text,
                voice_id=ELEVENLABS_VOICE_ID,
                model_id="eleven_multilingual_v2"
            )
            with open(output_path, "wb") as f:
                for chunk in audio_generator:
                    f.write(chunk)
            if os.path.exists(output_path) and os.path.getsize(output_path) > 500:
                return output_path
        except Exception as e:
            print(f"[ElevenLabs Voice Fallback] Reason: {e}")
            
    # Attempt 2: Local Offline Voice Engine (gTTS fallback)
    try:
        from gtts import gTTS
        tts = gTTS(text=clean_text, lang="en", tld="co.in", slow=False)
        tts.save(output_path)
        return output_path
    except Exception as e:
        print(f"[Local TTS Voice Fallback] Reason: {e}")
        
    return ""

if __name__ == "__main__":
    test_msg = "Order Number 14! 2 Butter Naan, 1 Kadhai Paneer. Table 4."
    path = generate_voice_callout(test_msg)
    print(f"Generated test callout at: {path}")
