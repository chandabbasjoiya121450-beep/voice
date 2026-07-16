import sys

# ─────────────────────────────────────────────────────────────────────────────
# COMPATIBILITY PATCH: Gradio 4.44.x uses Starlette's OLD TemplateResponse API:
#   TemplateResponse("template.html", {"request": req, ...})
# Starlette 0.41+ removed this positional style and now requires:
#   TemplateResponse(request=req, name="template.html", context={...})
# This patch makes both styles work transparently.
# ─────────────────────────────────────────────────────────────────────────────
try:
    import starlette.templating as _st
    _original_TemplateResponse = _st.Jinja2Templates.TemplateResponse

    def _compat_TemplateResponse(self, *args, **kwargs):
        # Old style: first arg is a string (template name)
        if args and isinstance(args[0], str):
            name = args[0]
            context = args[1] if len(args) > 1 else {}
            request = context.get("request") if isinstance(context, dict) else None
            ctx = {k: v for k, v in context.items() if k != "request"} if isinstance(context, dict) else {}
            try:
                return _original_TemplateResponse(
                    self, request=request, name=name, context=ctx,
                    *args[2:], **kwargs
                )
            except TypeError:
                return _original_TemplateResponse(self, *args, **kwargs)
        # New style or unknown — pass through unchanged
        return _original_TemplateResponse(self, *args, **kwargs)

    _st.Jinja2Templates.TemplateResponse = _compat_TemplateResponse
    print("Starlette TemplateResponse compatibility patch applied.")
except Exception as e:
    print(f"Could not apply TemplateResponse patch (non-critical): {e}")

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
import gradio as gr

os.environ["TTS_HOME"] = "/tmp/models"
os.environ["COQUI_TOS_AGREED"] = "1"

# Import backend FastAPI app
from backend.app import app as fastapi_app

# Minimal Gradio demo — full-screen iframe covers Gradio UI
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

    # Launch Gradio non-blocking — spaces SDK sets up ZeroGPU proxy here
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        prevent_thread_lock=True,
        show_error=True,
    )

    # After launch, safely inject backend routes into the live Gradio app
    if demo.app is not None:
        for route in fastapi_app.routes:
            demo.app.routes.append(route)
        print(f"[EchoVibe] {len(fastapi_app.routes)} backend routes registered.")
    else:
        print("[EchoVibe] WARNING: demo.app is None — backend routes not registered.")

    # Keep main thread alive forever
    demo.block_thread()
