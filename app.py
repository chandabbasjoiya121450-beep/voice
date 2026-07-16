try:
    import spaces
    print("ZeroGPU Spaces environment initialized at entrypoint.")
except ImportError:
    print("Running outside Hugging Face ZeroGPU environment.")

import os
import uvicorn
import gradio as gr

# Set cache directories to local folders inside Space before importing model
os.environ["TTS_HOME"] = "/code/models"
os.environ["COQUI_TOS_AGREED"] = "1"

# Import our FastAPI app
from backend.app import app as fastapi_app

# Create a minimal Gradio demo to satisfy Hugging Face ZeroGPU hooks and display our custom UI
with gr.Blocks(title="EchoVibe AI Studio") as demo:
    gr.HTML(
        "<iframe src='/studio/' style='position:fixed; top:0; left:0; width:100vw; height:100vh; border:none; margin:0; padding:0; z-index:999999;'></iframe>"
    )

# Mount the Gradio app to our FastAPI app at root '/'
app = gr.mount_gradio_app(fastapi_app, demo, path="/")

if __name__ == "__main__":
    # Hugging Face Spaces passes the port in the PORT environment variable (defaults to 7860)
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
