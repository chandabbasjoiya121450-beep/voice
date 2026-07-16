FROM python:3.10-slim

# Install system dependencies (FFmpeg for audio conversion)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /code

# Copy requirements file first
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install PyTorch CPU wheels (highly optimized and lightweight compared to GPU version)
RUN pip install --no-cache-dir torch torchaudio --index-url https://download.pytorch.org/whl/cpu

# Copy project files
COPY . .

# Create models and voices directories and set permissions for Hugging Face User 1000
RUN mkdir -p /code/models /code/voices /code/backend && \
    chmod -R 777 /code

# Set Hugging Face cache directory environments
ENV HOME=/code
ENV TTS_HOME=/code/models

# Expose Hugging Face Space port
EXPOSE 7860

# Run Uvicorn server on port 7860
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "7860"]
