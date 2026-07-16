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

# Set cache directories before importing model
os.environ["TTS_HOME"] = "/tmp/models"
os.environ["COQUI_TOS_AGREED"] = "1"

# Import our FastAPI backend app
from backend.app import app as fastapi_app

# Create the Gradio demo (iframe pointing to our custom frontend at /studio/)
with gr.Blocks(title="EchoVibe AI Studio") as demo:
    gr.HTML("""
        <style>
            body, .gradio-container, #component-0, .main {
                margin: 0 !important;
                padding: 0 !important;
                width: 100vw !important;
                height: 100vh !important;
                overflow: hidden !important;
                background: transparent !important;
            }
            footer { display: none !important; }
        </style>
        <iframe src='/studio/'
            style='position:fixed;top:0;left:0;width:100vw;height:100vh;border:none;z-index:999999;'>
        </iframe>
    """)

# Inject all our FastAPI routes into Gradio's internal FastAPI app
# This MUST happen before demo.launch() is called
for route in fastapi_app.routes:
    demo.app.routes.append(route)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    # demo.launch() blocks the main thread — this is what HF Spaces expects
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        show_error=True,
        prevent_thread_lock=False
    )
