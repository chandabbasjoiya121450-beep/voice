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

os.environ["TTS_HOME"] = "/tmp/models"
os.environ["COQUI_TOS_AGREED"] = "1"

# Import backend ASGI app
from backend.app import app as fastapi_app

# Minimal Gradio demo — iframe points to our custom frontend served at /studio/
with gr.Blocks(title="EchoVibe AI Studio") as demo:
    gr.HTML("""
        <style>
            body,.gradio-container,footer{margin:0!important;padding:0!important;overflow:hidden!important;}
            footer{display:none!important;}
        </style>
        <iframe src='/studio/'
            style='position:fixed;top:0;left:0;width:100vw;height:100vh;border:none;z-index:999999;'>
        </iframe>
    """)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))

    # Step 1: Launch Gradio non-blocking so HF/spaces SDK sets up its ZeroGPU proxy correctly.
    # Do NOT inject any routes yet — injecting before launch corrupts Gradio's Jinja2 cache.
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        prevent_thread_lock=True,   # non-blocking — we add routes right after
        show_error=True,
    )

    # Step 2: After the Gradio server is live, safely append our backend routes.
    # Starlette reads self.routes dynamically on every request, so no restart is needed.
    if demo.app is not None:
        for route in fastapi_app.routes:
            demo.app.routes.append(route)
        print(f"[EchoVibe] Backend routes registered ({len(fastapi_app.routes)} routes).")
    else:
        print("[EchoVibe] WARNING: demo.app is None — backend routes not registered.")

    # Step 3: Block the main thread forever so the process stays alive.
    demo.block_thread()
