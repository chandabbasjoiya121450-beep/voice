import os
import sys
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
MODELS_DIR = PROJECT_DIR / "models"
VOICES_DIR = PROJECT_DIR / "voices"

# Configure environments to avoid interactive prompts and override caches
os.environ["TTS_HOME"] = str(MODELS_DIR)
os.environ["COQUI_TOS_AGREED"] = "1"

def run_test():
    print("Loading Coqui XTTS v2...")
    try:
        from TTS.api import TTS
    except ImportError as e:
        print(f"Error: Coqui TTS is not installed in venv! Detail: {e}")
        sys.exit(1)

    speaker_wav = VOICES_DIR / "sample_narrator.wav"
    output_wav = BASE_DIR / "test_synthesis.wav"

    if not speaker_wav.exists():
        print(f"Error: Reference speaker audio '{speaker_wav}' not found.")
        print("Please run the backend server and seed the sample voice first.")
        sys.exit(1)

    # Initialize model on CPU
    print("Initializing XTTS model (downloading v2 weights if not present)...")
    try:
        tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", gpu=False)
    except Exception as e:
        print(f"Failed to load/download model: {e}")
        sys.exit(1)

    text = "Hello, this is Echo Vibe Studio. The zero shot voice cloning and advanced speech engine is running offline."
    print(f"Synthesizing text: '{text}' using reference voice '{speaker_wav.name}'...")
    
    try:
        tts.tts_to_file(
            text=text,
            speaker_wav=str(speaker_wav),
            language="en",
            file_path=str(output_wav)
        )
        print(f"Synthesis finished! Output saved to: {output_wav}")
        if output_wav.exists() and output_wav.stat().st_size > 1000:
            print("Verification passed! Wave file is valid and contains audio data.")
        else:
            print("Verification failed: Wave file is empty or too small.")
    except Exception as e:
        print(f"Synthesis failed with error: {e}")

if __name__ == "__main__":
    run_test()
