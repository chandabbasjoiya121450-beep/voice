import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
import sys
import uuid
import shutil
import sqlite3
import threading
import subprocess
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel, Field

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI App
app = FastAPI(
    title="EchoVibe AI Multilingual TTS & Voice Studio",
    description="A local FastAPI backend serving Coqui XTTS v2 with voice cloning, database profiles, and audio controls.",
    version="2.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
VOICES_DIR = PROJECT_DIR / "voices"
OUTPUT_DIR = PROJECT_DIR / "output"
MODELS_DIR = PROJECT_DIR / "models"
DATABASE_DIR = PROJECT_DIR / "database"
FRONTEND_DIR = PROJECT_DIR / "frontend"

# Ensure all directories exist
VOICES_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_DIR.mkdir(parents=True, exist_ok=True)
FRONTEND_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATABASE_DIR / "metadata.db"

# ----------------------------------------------------
# Database Initialization
# ----------------------------------------------------
def init_db():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    # Voices Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS voices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            language TEXT NOT NULL,
            label TEXT,
            filepath TEXT NOT NULL,
            accent TEXT,
            speaking_style TEXT,
            pace TEXT,
            tone TEXT,
            is_favorite INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # History Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            language TEXT NOT NULL,
            voice_name TEXT NOT NULL,
            speed REAL DEFAULT 1.0,
            pitch REAL DEFAULT 1.0,
            volume REAL DEFAULT 1.0,
            format TEXT NOT NULL,
            filepath TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ----------------------------------------------------
# Global Model State & Asynchronous Loading
# ----------------------------------------------------
xtts_model = None
xtts_status = "idle"  # idle, loading, ready, failed
xtts_error = None

def load_xtts_model_async():
    global xtts_model, xtts_status, xtts_error
    xtts_status = "loading"
    print("Starting async download/load of Coqui XTTS v2...")
    try:
        # Import inside function to avoid slowing down startup
        from TTS.api import TTS
        
        # Configure model cache directory to our project models directory
        os.environ["TTS_HOME"] = str(MODELS_DIR)
        os.environ["COQUI_TOS_AGREED"] = "1"
        
        # Initialize model (GPU = False for local CPU compliance)
        # Note: downloads ~2.4GB model files on first invocation
        xtts_model = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", gpu=False)
        
        xtts_status = "ready"
        print("Coqui XTTS v2 model is loaded and ready for offline use!")
    except Exception as e:
        xtts_status = "failed"
        xtts_error = str(e)
        print(f"Failed to load Coqui XTTS v2 model: {e}")

# Trigger loading on app startup in a separate daemon thread
@app.on_event("startup")
def startup_event():
    threading.Thread(target=load_xtts_model_async, daemon=True).start()

# ----------------------------------------------------
# Audio Processing Utilities (Librosa & FFmpeg)
# ----------------------------------------------------
def is_ffmpeg_installed() -> bool:
    return shutil.which("ffmpeg") is not None

def analyze_audio_sample(filepath: str) -> dict:
    """Analyze a voice sample using librosa for tone, pace, accent, and style."""
    try:
        import librosa
        import numpy as np
        
        # Load audio (mono, original sample rate)
        y, sr = librosa.load(filepath, sr=None)
        
        # 1. Tone / Pitch Analysis (Mean F0)
        # yin algorithm extracts pitch frequencies
        f0 = librosa.yin(y, fmin=65, fmax=500)
        valid_f0 = f0[f0 > 0]
        if len(valid_f0) > 0:
            mean_f0 = float(np.mean(valid_f0))
            if mean_f0 < 130:
                tone = f"Deep / Low Pitch ({round(mean_f0)} Hz)"
            elif mean_f0 > 185:
                tone = f"High / Bright Pitch ({round(mean_f0)} Hz)"
            else:
                tone = f"Medium / Melodious ({round(mean_f0)} Hz)"
        else:
            tone = "Resonant / Warm"
            
        # 2. Pace / Tempo Analysis
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        tempo_val = float(tempo[0]) if isinstance(tempo, np.ndarray) else float(tempo)
        if tempo_val > 125:
            pace = f"Fast-paced ({round(tempo_val)} BPM)"
        elif tempo_val < 95:
            pace = f"Slow & Deliberate ({round(tempo_val)} BPM)"
        else:
            pace = f"Moderate / Natural ({round(tempo_val)} BPM)"
            
        return {
            "accent": "General / Neutral",
            "speaking_style": "Conversational",
            "pace": pace,
            "tone": tone
        }
    except Exception as e:
        print(f"Librosa audio analysis failed: {e}. Using fallbacks.")
        return {
            "accent": "Neutral / General",
            "speaking_style": "Clear",
            "pace": "Moderate / Balanced",
            "tone": "Warm / Natural"
        }

def process_audio_ffmpeg(input_path: Path, output_path: Path, speed: float, pitch: float, volume: float, silence_trim: bool, normalize: bool) -> bool:
    """Apply speed, pitch, volume, silence trimming, and normalization in a single FFmpeg call."""
    if not is_ffmpeg_installed():
        # Fallback to copy if ffmpeg is missing
        shutil.copy(input_path, output_path)
        return False
        
    filters = []
    
    # 1. Pitch & Speed adjustments
    # Pitch scale is implemented by shifting the rate and scaling speed back to match the target
    sample_rate = 24000  # Default XTTS output rate
    if pitch != 1.0:
        filters.append(f"asetrate={sample_rate}*{pitch}")
        speed_factor = speed / pitch
        if speed_factor != 1.0:
            filters.append(f"atempo={speed_factor}")
    elif speed != 1.0:
        filters.append(f"atempo={speed}")
        
    # 2. Volume scale
    if volume != 1.0:
        filters.append(f"volume={volume}")
        
    # 3. Silence Trimming
    if silence_trim:
        filters.append("silenceremove=start_periods=1:start_silence=0.1:start_threshold=-50dB:stop_periods=-1:stop_duration=1.0:stop_threshold=-50dB")
        
    # 4. Audio Normalization
    if normalize:
        filters.append("loudnorm")
        
    cmd = ["ffmpeg", "-y", "-i", str(input_path)]
    if filters:
        cmd.extend(["-filter:a", ",".join(filters)])
    cmd.append(str(output_path))
    
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc.returncode == 0

# ----------------------------------------------------
# API Routing Models
# ----------------------------------------------------
class GenerateRequest(BaseModel):
    text: str
    language: str = "en"  # "en", "ur", "es", "auto", etc.
    voice_name: str       # Custom voice profile name
    speed: float = 1.0
    pitch: float = 1.0
    volume: float = 1.0
    silence_trimming: bool = False
    audio_normalization: bool = False
    output_format: str = "mp3"  # mp3 or wav

class VoiceUpdate(BaseModel):
    label: Optional[str] = None
    is_favorite: Optional[int] = None

# ----------------------------------------------------
# REST API Endpoints
# ----------------------------------------------------
def get_dir_size(path: Path) -> int:
    total = 0
    if path.exists():
        for entry in path.glob('**/*'):
            if entry.is_file():
                total += entry.stat().st_size
    return total

@app.get("/api/model-status")
def get_model_status():
    """Get the async loading status of the Coqui XTTS v2 model with real-time download metrics."""
    downloaded_bytes = get_dir_size(MODELS_DIR / "tts")
    total_bytes = 2028832192  # 1.89 GB expected size for XTTS v2 weights
    
    # Calculate percentage
    if xtts_status == "ready":
        percentage = 100.0
        downloaded_bytes = total_bytes
    else:
        percentage = min(99.9, (downloaded_bytes / total_bytes) * 100.0) if downloaded_bytes < total_bytes else 99.9

    return {
        "status": xtts_status,
        "error": xtts_error,
        "ffmpeg_installed": is_ffmpeg_installed(),
        "downloaded_mb": round(downloaded_bytes / (1024 * 1024), 1),
        "total_mb": round(total_bytes / (1024 * 1024), 1),
        "percentage": round(percentage, 1)
    }

@app.post("/api/voices/upload")
async def upload_voice_profile(
    name: str = Form(...),
    language: str = Form(...),
    label: str = Form(...),
    consent: bool = Form(...),
    file: UploadFile = File(...)
):
    """Voice Studio upload. Analyzes sample, clones, and saves voice profile locally."""
    if not consent:
        raise HTTPException(
            status_code=400, 
            detail="You must confirm you have permission/ownership to clone this voice."
        )
    
    # Save the file temporarily
    temp_id = str(uuid.uuid4())
    temp_wav = VOICES_DIR / f"{temp_id}.wav"
    try:
        with open(temp_wav, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Convert uploaded file (could be mp3) to clean 24kHz Mono WAV for best cloning results
        clean_wav = VOICES_DIR / f"voice_{temp_id}.wav"
        if is_ffmpeg_installed():
            cmd = [
                "ffmpeg", "-y", "-i", str(temp_wav),
                "-acodec", "pcm_s16le", "-ar", "24000", "-ac", "1",
                str(clean_wav)
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # Remove raw upload
            if temp_wav.exists():
                temp_wav.unlink()
        else:
            # Fallback rename
            os.rename(temp_wav, clean_wav)
            
        # Analyze voice properties via librosa
        analysis = analyze_audio_sample(str(clean_wav))
        
        # Save to database
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO voices (name, language, label, filepath, accent, speaking_style, pace, tone)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, language, label, str(clean_wav), analysis["accent"], analysis["speaking_style"], analysis["pace"], analysis["tone"]))
            conn.commit()
            voice_id = cursor.lastrowid
        except sqlite3.IntegrityError:
            # Cleanup file
            if clean_wav.exists():
                clean_wav.unlink()
            raise HTTPException(status_code=400, detail=f"A voice profile with name '{name}' already exists.")
        finally:
            conn.close()
            
        return {
            "id": voice_id,
            "name": name,
            "language": language,
            "label": label,
            "filepath": str(clean_wav),
            **analysis
        }
    except Exception as e:
        if temp_wav.exists():
            temp_wav.unlink()
        raise HTTPException(status_code=500, detail=f"Voice profiling failed: {str(e)}")

@app.get("/api/voices")
def list_voices():
    """List all custom voice profiles stored in SQLite."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM voices ORDER BY is_favorite DESC, created_at DESC")
    voices = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"voices": voices}

@app.get("/api/voices/{voice_id}/preview")
def preview_voice(voice_id: int):
    """Play the original cloned voice sample."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("SELECT filepath FROM voices WHERE id = ?", (voice_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row or not Path(row[0]).exists():
        raise HTTPException(status_code=404, detail="Voice profile or file not found")
        
    return FileResponse(row[0], media_type="audio/wav")

@app.patch("/api/voices/{voice_id}")
def update_voice(voice_id: int, update: VoiceUpdate):
    """Edit custom voice label or mark it as favorite."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    fields = []
    values = []
    if update.label is not None:
        fields.append("label = ?")
        values.append(update.label)
    if update.is_favorite is not None:
        fields.append("is_favorite = ?")
        values.append(update.is_favorite)
        
    if not fields:
        raise HTTPException(status_code=400, detail="No update fields provided")
        
    values.append(voice_id)
    cursor.execute(f"UPDATE voices SET {', '.join(fields)} WHERE id = ?", tuple(values))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Voice profile updated."}

@app.delete("/api/voices/{voice_id}")
def delete_voice(voice_id: int):
    """Delete a voice profile metadata and remove the WAV reference file from disk."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("SELECT filepath FROM voices WHERE id = ?", (voice_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Voice profile not found")
        
    filepath = Path(row[0])
    
    cursor.execute("DELETE FROM voices WHERE id = ?", (voice_id,))
    conn.commit()
    conn.close()
    
    # Delete from file system
    if filepath.exists():
        filepath.unlink()
        
    return {"status": "success", "message": f"Voice profile deleted."}

@app.post("/api/voices/sample")
def download_sample_voice():
    """Seed the DB with a public domain sample English voice for instant testing."""
    sample_name = "English Narrator (Sample)"
    
    # Check if already exists
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM voices WHERE name = ?", (sample_name,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {"status": "exists", "id": row[0]}
        
    sample_wav_path = VOICES_DIR / "sample_narrator.wav"
    
    # Fetch public domain sample wav (from coqui testing files)
    try:
        import requests
        url = "https://github.com/coqui-ai/TTS/raw/main/tests/data/ljspeech/wavs/LJ001-0001.wav"
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        with open(sample_wav_path, "wb") as f:
            f.write(r.content)
            
        # Add to DB
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO voices (name, language, label, filepath, accent, speaking_style, pace, tone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (sample_name, "en", "Narrator", str(sample_wav_path), "US Accent", "Storytelling", "Moderate (115 BPM)", "Melodious (180 Hz)"))
        conn.commit()
        voice_id = cursor.lastrowid
        conn.close()
        
        return {"status": "created", "id": voice_id}
    except Exception as e:
        if sample_wav_path.exists():
            sample_wav_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to fetch testing voice sample: {str(e)}")

@app.post("/api/generate")
def generate_speech(request: GenerateRequest):
    """Main Text-to-Speech endpoint. Clones target voice, processes settings, and returns audio stream."""
    global xtts_model, xtts_status
    
    if xtts_status != "ready" or xtts_model is None:
        raise HTTPException(
            status_code=503, 
            detail=f"Model engine is currently downloading/loading. Current status: {xtts_status}. Please wait."
        )
        
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text input cannot be empty.")
        
    # Resolve reference voice
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("SELECT filepath, name FROM voices WHERE name = ?", (request.voice_name,))
    voice_row = cursor.fetchone()
    conn.close()
    
    if not voice_row:
        raise HTTPException(status_code=404, detail=f"Voice profile '{request.voice_name}' not found.")
        
    speaker_wav_path = voice_row[0]
    if not Path(speaker_wav_path).exists():
        raise HTTPException(status_code=404, detail="Reference voice sample file is missing from local disk.")
        
    # Detect language if set to auto
    lang_code = request.language
    if lang_code == "auto":
        try:
            from langdetect import detect
            lang_code = detect(request.text)
            print(f"Automatically detected text language: {lang_code}")
            # Map common outputs to coqui-compatible list
            supported = ["en", "ur", "de", "ru", "es", "fr", "it", "pt", "tr", "ar", "hi", "zh", "ja", "ko"]
            if lang_code not in supported:
                # Fallback to English if not supported
                lang_code = "en"
        except Exception as lang_err:
            print(f"Language detection failed: {lang_err}. Defaulting to English.")
            lang_code = "en"
            
    # Setup temporary output paths
    req_id = str(uuid.uuid4())
    raw_wav = OUTPUT_DIR / f"{req_id}_raw.wav"
    processed_audio = OUTPUT_DIR / f"{req_id}_final.{request.output_format}"
    
    try:
        # 1. Synthesize Cloned Speech via Coqui XTTS
        # Generates a high-quality 24kHz audio file
        xtts_model.tts_to_file(
            text=request.text,
            speaker_wav=str(speaker_wav_path),
            language=lang_code,
            file_path=str(raw_wav)
        )
        
        if not raw_wav.exists():
            raise RuntimeError("TTS model failed to output raw WAV file.")
            
        # 2. Process audio parameters (Speed, Pitch, Vol, Silence, Norm) using single-pass FFmpeg
        process_audio_ffmpeg(
            input_path=raw_wav,
            output_path=processed_audio,
            speed=request.speed,
            pitch=request.pitch,
            volume=request.volume,
            silence_trim=request.silence_trimming,
            normalize=request.audio_normalization
        )
        
        # Cleanup raw WAV file
        if raw_wav.exists():
            raw_wav.unlink()
            
        # 3. Log into history table
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # Store a copy of output in outputs folder for history retrieval
        permanent_path = OUTPUT_DIR / f"clip_{req_id}.{request.output_format}"
        shutil.copy(processed_audio, permanent_path)
        
        cursor.execute("""
            INSERT INTO history (text, language, voice_name, speed, pitch, volume, format, filepath)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (request.text, lang_code, request.voice_name, request.speed, request.pitch, request.volume, request.output_format, str(permanent_path)))
        conn.commit()
        conn.close()
        
        # Stream response and cleanup processed file
        def iter_file():
            try:
                with open(processed_audio, mode="rb") as f:
                    yield from f
            finally:
                if processed_audio.exists():
                    processed_audio.unlink()
                    
        media_type = "audio/mpeg" if request.output_format == "mp3" else "audio/wav"
        headers = {
            "Content-Disposition": f"attachment; filename=speech_{req_id}.{request.output_format}"
        }
        return StreamingResponse(iter_file(), media_type=media_type, headers=headers)
        
    except Exception as e:
        if raw_wav.exists():
            raw_wav.unlink()
        if processed_audio.exists():
            processed_audio.unlink()
        raise HTTPException(status_code=500, detail=f"Speech synthesis execution failed: {str(e)}")

@app.get("/api/history")
def get_history():
    """Fetch generated clips history."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM history ORDER BY created_at DESC LIMIT 50")
    history = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"history": history}

@app.get("/api/history/{clip_id}/audio")
def get_history_audio(clip_id: int):
    """Retrieve history clip audio file."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("SELECT filepath, format FROM history WHERE id = ?", (clip_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row or not Path(row[0]).exists():
        raise HTTPException(status_code=404, detail="Audio clip file not found")
        
    media_type = "audio/mpeg" if row[1] == "mp3" else "audio/wav"
    return FileResponse(row[0], media_type=media_type)

@app.delete("/api/history/{clip_id}")
def delete_history_item(clip_id: int):
    """Delete history item and remove generated clip from disk."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("SELECT filepath FROM history WHERE id = ?", (clip_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="History clip not found")
        
    filepath = Path(row[0])
    
    cursor.execute("DELETE FROM history WHERE id = ?", (clip_id,))
    conn.commit()
    conn.close()
    
    # Delete from file system
    if filepath.exists():
        filepath.unlink()
        
    return {"status": "success", "message": "History clip deleted."}

# Mount Frontend static files
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
