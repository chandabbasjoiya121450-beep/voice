import sys
try:
    import spaces
    print("ZeroGPU Spaces environment initialized at entrypoint.")
except ImportError:
    class MockSpaces:
        @staticmethod
        def GPU(func=None, duration=None):
            if func is None:
                def decorator(f):
                    return f
                return decorator
            return func
    sys.modules["spaces"] = MockSpaces
    import spaces
    print("Running in non-ZeroGPU environment (standard local CPU/GPU).")

import os
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

# Create the Gradio FastAPI application
app = gr.routes.App.create_app(demo)

# Inject all routes from our FastAPI backend app directly into the Gradio app
# This merges our API endpoints and '/studio' static mount into the Gradio app
for route in fastapi_app.routes:
    app.routes.append(route)

# Link the customized app back to demo.app so that demo.launch() uses it
demo.app = app

if __name__ == "__main__":
    # Hugging Face Spaces passes the port in the PORT environment variable (defaults to 7860)
    port = int(os.environ.get("PORT", 7860))
    
    # Launch the Gradio application using demo.launch() to satisfy Hugging Face platform requirements
    demo.launch(server_name="0.0.0.0", server_port=port, prevent_thread_lock=False)
