try:
    import spaces
    print("ZeroGPU Spaces environment initialized at entrypoint.")
except ImportError:
    print("Running outside Hugging Face ZeroGPU environment.")

import os
import uvicorn

# Set cache directories to local folders inside Space before importing model
os.environ["TTS_HOME"] = "/code/models"
os.environ["COQUI_TOS_AGREED"] = "1"

# Import our FastAPI app
from backend.app import app

if __name__ == "__main__":
    # Hugging Face Spaces passes the port in the PORT environment variable (defaults to 7860)
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
