---
title: EchoVibe AI Studio
emoji: 🎙️
colorFrom: indigo
colorTo: purple
sdk: gradio
sdk_version: 4.44.1
app_file: app.py
pinned: false
---

# EchoVibe Studio - Premium AI Voice Cloning & Multilingual TTS

EchoVibe Studio is a complete, free, fully offline-capable Text-to-Speech (TTS) web application built using Python (FastAPI) and a modern glassmorphic HTML5/CSS3/JavaScript frontend. It leverages **Coqui XTTS v2** for zero-shot voice cloning and synthesis in 14+ languages.

## Features
- **Voice Studio Cloning:** Upload a clean 30–120 second voice sample, confirm ownership consent, and extract tone, pace, and style properties locally using `librosa`.
- **Custom Voices Library:** Store, favorite, preview, rename, and manage custom voice profiles.
- **Multilingual Support:** English, Urdu, Spanish, French, German, Italian, Portuguese, Russian, Turkish, Arabic, Hindi, Chinese, Japanese, and Korean.
- **Auto Language Detection:** Automatically identifies text language using `langdetect`.
- **Advanced Audio FX:** Fine-tune speaking speed, pitch scaling, and volume, along with silence trimming and audio normalization using a single-pass custom FFmpeg graph.
- **Visualizer Playback:** custom-styled audio player with staggered visualizer waves dancing in sync with cloned speech.
- **Dual Themes:** Seamlessly toggle between Dark Mode and Light Mode with local persistence.
- **Zero Paid APIs:** Runs completely offline on local CPU/GPU with no internet required after model weights are cached.

---

## Project Structure
```text
tts-project/
├── frontend/
│   ├── index.html     # Glassmorphic user interface (tabs, studio form, consent)
│   ├── style.css      # Dark & Light variables, visualizer, keyframes
│   └── script.js      # Form handler, REST client, status checker
├── backend/
│   ├── app.py         # FastAPI main app, SQLite manager, Librosa analyzer, FFmpeg pipe
│   ├── models/        # Location where XTTS v2 models are downloaded
│   ├── output/        # Temporary audio generation cache
│   └── test_tts.py    # Offline speech synthesis testing script
├── database/
│   └── metadata.db    # SQLite database storing voice profiles and log history
├── voices/
│   └── ...            # Uploaded cloned voice sample files (.wav)
├── requirements.txt   # Backend library dependencies
└── README.md          # Setup & execution instructions
```

---

## Step-by-Step Installation Guide

### 1. Install System Dependencies

#### **FFmpeg Setup**
FFmpeg is required to process volume, speed, pitch, silence removal, and MP3 encoding.

- **Debian/Ubuntu:**
  ```bash
  sudo apt-get update
  sudo apt-get install -y ffmpeg
  ```
- **macOS:**
  ```bash
  brew install ffmpeg
  ```
- **Windows (winget):**
  ```cmd
  winget install Gyan.FFmpeg
  ```

#### **Espeak-ng Setup**
Required by Coqui TTS for text tokenization.
- **Debian/Ubuntu:**
  ```bash
  sudo apt-get install -y espeak-ng espeak-ng-data
  ```
- **macOS:**
  ```bash
  brew install espeak-ng
  ```

---

### 2. Set Up Virtual Environment

Navigate to the project folder, initialize a virtual environment, and install dependencies:

```bash
cd tts-project
python3 -m venv venv
```

Activate the virtual environment:
- **Linux/macOS:**
  ```bash
  source venv/bin/activate
  ```
- **Windows (CMD):**
  ```cmd
  venv\Scripts\activate.bat
  ```

Install python requirements:
```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

---

### 3. Model Weights Installation

The backend automatically handles downloading the Coqui XTTS v2 model from Hugging Face on its first run (approx 2.4 GB). 

If you are setting this up in a completely air-gapped/offline environment, download the files from the Hugging Face repository `coqui/XTTS-v2` and place them in:
- **Linux/macOS:** `~/.local/share/tts/tts_models--multilingual--multi-dataset--xtts_v2/`
- **Windows:** `%APPDATA%\tts\tts_models--multilingual--multi-dataset--xtts_v2\`

---

### 4. Running the Application Locally

Start the Uvicorn server:
```bash
uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
```

Navigate to **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser.

- On first startup, the server starts loading/downloading the model weights. The UI footer will display **"Downloading XTTS v2 (~2.4GB)..."**.
- Click **"Load English Sample Voice (Testing)"** in the **My Voices** tab to load a public domain sample narrator voice instantly for testing.
- Head to the **Voice Studio** tab to clone your first custom voice!

---

## Troubleshooting Guide

#### **Q: The server starts, but synthesis fails with an Import or PyTorch error**
**A:** Ensure your virtual environment is activated and that PyTorch has installed successfully for your system CPU/GPU. You can test your local PyTorch installation with:
```bash
python -c "import torch; print(torch.cuda.is_available())"
```

#### **Q: Speech generation is taking a long time**
**A:** Coqui XTTS v2 is a deep learning transformer model. If running on a CPU without a dedicated NVIDIA GPU, generation will take approximately 10–25 seconds per short sentence. For production use, install PyTorch with CUDA support and configure `gpu=True` in `backend/app.py`.

#### **Q: Uploading voice clips throws an ethics error**
**A:** The Voice Studio enforces ethical voice cloning. The "Create Voice Profile" button remains disabled until you check the consent verification box confirming you have legal permissions to clone the speaker's voice.
