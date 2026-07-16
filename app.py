import sys

# ─────────────────────────────────────────────────────────────────────────────
# COMPATIBILITY PATCH: Gradio 4.44.x + Starlette 0.41+ TemplateResponse fix
# ─────────────────────────────────────────────────────────────────────────────
try:
    import starlette.templating as _st
    _original_TemplateResponse = _st.Jinja2Templates.TemplateResponse

    def _compat_TemplateResponse(self, *args, **kwargs):
        if args and isinstance(args[0], str):
            name = args[0]
            context = args[1] if len(args) > 1 else {}
            request = context.get("request") if isinstance(context, dict) else None
            ctx = {k: v for k, v in context.items() if k != "request"} if isinstance(context, dict) else {}
            try:
                return _original_TemplateResponse(self, request=request, name=name, context=ctx)
            except TypeError:
                return _original_TemplateResponse(self, *args, **kwargs)
        return _original_TemplateResponse(self, *args, **kwargs)

    _st.Jinja2Templates.TemplateResponse = _compat_TemplateResponse
    print("Starlette TemplateResponse compatibility patch applied.")
except Exception as e:
    print(f"Could not apply TemplateResponse patch: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# ZeroGPU spaces mock (for local CPU testing)
# ─────────────────────────────────────────────────────────────────────────────
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
import mimetypes
from pathlib import Path
from fastapi import Request
from fastapi.responses import FileResponse, HTMLResponse, Response
import gradio as gr

os.environ["TTS_HOME"] = "/tmp/models"
os.environ["COQUI_TOS_AGREED"] = "1"

# Frontend directory (shipped with the code — always present)
FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"

# Import backend FastAPI app
from backend.app import app as fastapi_app

# ─────────────────────────────────────────────────────────────────────────────
# Add explicit /studio/* route to the FastAPI backend app BEFORE building Gradio
# This is more reliable than injecting StaticFiles Mount into Gradio's router
# ─────────────────────────────────────────────────────────────────────────────
@fastapi_app.get("/studio/{filepath:path}", include_in_schema=False)
async def serve_studio_files(filepath: str):
    """Serve frontend static files from /studio/ path."""
    if not filepath or filepath == "/":
        filepath = "index.html"
    file_path = FRONTEND_DIR / filepath
    if file_path.exists() and file_path.is_file():
        media_type, _ = mimetypes.guess_type(str(file_path))
        return FileResponse(str(file_path), media_type=media_type or "application/octet-stream")
    # Fallback to index.html for SPA routing
    index = FRONTEND_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index), media_type="text/html")
    return Response("Not found", status_code=404)

@fastapi_app.get("/studio", include_in_schema=False)
async def serve_studio_root():
    """Redirect /studio to /studio/index.html"""
    index = FRONTEND_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index), media_type="text/html")
    return Response("Frontend not found", status_code=404)

# ─────────────────────────────────────────────────────────────────────────────
# Minimal Gradio demo — full-screen iframe covers Gradio UI
# ─────────────────────────────────────────────────────────────────────────────
with gr.Blocks(title="EchoVibe AI Studio") as demo:
    gr.HTML("""
        <style>
            body,.gradio-container,footer{margin:0!important;padding:0!important;overflow:hidden!important;}
            footer{display:none!important;}
        </style>
        <iframe src='/studio'
            style='position:fixed;top:0;left:0;width:100vw;height:100vh;border:none;z-index:999999;'>
        </iframe>
    """)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))

    # Launch Gradio non-blocking so spaces SDK sets up ZeroGPU proxy
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        prevent_thread_lock=True,
        show_error=True,
    )

    # After launch, inject ALL backend API routes into the live Gradio app
    # We skip StaticFiles Mount objects — those are handled by FileResponse routes above
    if demo.app is not None:
        from starlette.routing import Mount
        count = 0
        for route in fastapi_app.routes:
            if not isinstance(route, Mount):
                demo.app.routes.append(route)
                count += 1
        print(f"[EchoVibe] {count} API routes registered in Gradio app.")
    else:
        print("[EchoVibe] WARNING: demo.app is None.")

    demo.block_thread()
