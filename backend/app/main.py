import logging
import os
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings
from app.db.session import engine, Base
import app.models  # Ensure all models are registered
from app.core.privacy import PrivacyLogFilter

from app.api.auth import router as auth_router
from app.api.tracker import router as tracker_router
from app.api.pregnancy import router as pregnancy_router
from app.api.pcos import router as pcos_router
from app.api.safety import router as safety_router
from app.api.chat import router as chat_router
from app.api.voice import router as voice_router

# Configure privacy-preserving logging
root_logger = logging.getLogger()
privacy_filter = PrivacyLogFilter()
root_logger.addFilter(privacy_filter)
for handler in root_logger.handlers:
    handler.addFilter(privacy_filter)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="Privacy-preserving Bangla AI voice assistant for menstrual health and maternal wellness.",
    version="1.0.0"
)

# CORS Middleware (supports mobile apps, PWAs and local dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth_router)
app.include_router(tracker_router)
app.include_router(pregnancy_router)
app.include_router(pcos_router)
app.include_router(safety_router)
app.include_router(chat_router)
app.include_router(voice_router)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "privacy": "verified_no_pii"
    }

@app.get("/favicon.ico")
def get_favicon():
    svg_icon = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><circle cx='50' cy='50' r='48' fill='#C45B7A'/><text x='50' y='65' font-size='45' text-anchor='middle' fill='white'>🌸</text></svg>"""
    return Response(content=svg_icon, media_type="image/svg+xml")

# Serve PWA static assets if directory exists
PWA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "pwa")
if os.path.exists(PWA_DIR):
    app.mount("/pwa", StaticFiles(directory=PWA_DIR), name="pwa")

    @app.get("/")
    def serve_pwa_root():
        index_file = os.path.join(PWA_DIR, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"message": "Shoi API is running."}
