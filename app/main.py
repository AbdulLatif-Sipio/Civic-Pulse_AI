from starlette.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, PlainTextResponse, Response, RedirectResponse
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import init_db
from app.utils.file_handler import ensure_upload_dirs
from app.routers import submissions, tickets, stats, dashboard, admin_tools

# Configure logging format
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("cleancity")

# Ensure database tables and media directories exist upon module load
ensure_upload_dirs()
init_db()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager:
    Initializes database tables, composite indices, and upload directories on startup.
    """
    logger.info("Initializing CleanCity Copilot Backend Engine...")
    ensure_upload_dirs()
    init_db()
    logger.info("Database and media storage directories initialized successfully.")
    yield
    logger.info("CleanCity Copilot Backend shutting down.")


# Initialize FastAPI Application with Custom Branding
app = FastAPI(
    title="🏙️ " + settings.APP_NAME,
    version="1.0.0",
    description="""
# 🚀 CleanCity Copilot — AI Civic Triage & Geospatial Routing Engine
### *Alibaba Cloud AI Hackathon 2026*

CleanCity Copilot bridges citizen submissions with municipal dispatch using:
- **Speech-to-Text**: Urdu/Roman Urdu transcription & English translation (Whisper)
- **Multimodal AI**: Vision LLM categorization & automated tool/crew action plans
- **50-Meter Geo-Deduplication**: Haversine spatial-temporal clustering in SQLite
- **Built-in 3D Web Dashboard**: Interactive Cyberpunk UI served directly at [`/dashboard`](/dashboard)

---
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Attach SlowAPI Rate Limiter to application state
app.state.limiter = submissions.limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security & Force HTTPS Middleware (Item 5)
@app.middleware("http")
async def security_and_https_headers_middleware(request: Request, call_next):
    proto = request.headers.get("x-forwarded-proto", "").lower()
    if proto == "http" and getattr(settings, "FORCE_HTTPS", False):
        url = request.url.replace(scheme="https")
        return RedirectResponse(url=str(url), status_code=status.HTTP_308_PERMANENT_REDIRECT)

    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# GZip Compression Middleware (Item 12)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Configure CORS Middleware (Strictly restricted to configured origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if settings.CORS_ORIGINS != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

if not os.path.exists("static"):
    os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Mount local media directory for serving images and audio files
if not os.path.exists(settings.UPLOAD_DIR):
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

app.mount("/media", StaticFiles(directory=settings.UPLOAD_DIR), name="media")


# Security Hardening: Global exception handler to prevent leaking internal traces
@app.exception_handler(Exception)
async def global_unhandled_exception_handler(request: Request, exc: Exception):
    # Pass through standard HTTP errors, validation errors, and rate limit errors
    if isinstance(exc, (HTTPException, StarletteHTTPException, RequestValidationError, RateLimitExceeded)):
        raise exc

    logger.error(f"Unhandled server error processing {request.method} {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred. Please contact municipal system administration."
        }
    )


# Health Check Endpoint
@app.get("/api/health", tags=["Health"])
async def health_check():
    """Health check endpoint to verify backend operational readiness."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "environment": settings.APP_ENV
    }


# Include Application Routers

# Favicon Route (Item 9)
@app.get("/favicon.ico", include_in_schema=False)
async def favicon_route():
    for fav in ["favicon.ico", "static/favicon.ico"]:
        if os.path.exists(fav):
            return FileResponse(fav, media_type="image/x-icon")
    raise HTTPException(status_code=404, detail="Favicon not found")

# Custom 404 & 500 HTML Exception Handlers (Item 15)
@app.exception_handler(404)
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        if "text/html" in request.headers.get("accept", ""):
            tpl = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "templates", "404.html")
            if os.path.exists(tpl):
                with open(tpl, "r", encoding="utf-8") as f:
                    return HTMLResponse(content=f.read(), status_code=404)
        return JSONResponse(status_code=404, content={"status": "error", "status_code": 404, "detail": exc.detail or "Not Found"})
    elif exc.status_code == 500:
        if "text/html" in request.headers.get("accept", ""):
            tpl = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "templates", "500.html")
            if os.path.exists(tpl):
                with open(tpl, "r", encoding="utf-8") as f:
                    return HTMLResponse(content=f.read(), status_code=500)
        return JSONResponse(status_code=500, content={"status": "error", "status_code": 500, "detail": "Internal server error occurred."})
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

app.include_router(dashboard.router)
app.include_router(submissions.router)
app.include_router(tickets.router)
app.include_router(stats.router)
app.include_router(admin_tools.router)
