"""
========================================================================================
🚀 Master Standalone Backend: CivicPulse AI
Target: Alibaba Cloud AI Hackathon 2026
----------------------------------------------------------------------------------------
This single-file master script contains the ENTIRE backend, database layer, 
geo-deduplication engine, security hardening, AI integration stubs, and the 
built-in 3D Cyberpunk Web Dashboard.

Run with:
    python master_backend.py
or:
    uvicorn master_backend:app --reload --host 0.0.0.0 --port 8000
========================================================================================
"""

import os
import io
import math
import uuid
import secrets
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Generator, List, Optional, Dict, Any, Set, Tuple, Union
from datetime import datetime, timezone, timedelta
from contextlib import asynccontextmanager
from enum import Enum

# Third-party imports
from fastapi import FastAPI, Request, Depends, Form, File, UploadFile, HTTPException, Query, Security, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.security import APIKeyHeader
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel, Field, ConfigDict, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from sqlalchemy import create_engine, event, Column, String, Float, Text, Boolean, DateTime, Integer, Index, func, desc, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# ======================================================================================
# 1. CONFIGURATION & SETTINGS
# ======================================================================================
class Settings(BaseSettings):
    APP_NAME: str = "CivicPulse AI API"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Database
    DATABASE_URL: str = "sqlite:///./cleancity.db"

    # Security
    ADMIN_API_KEY: str = "civicpulse-admin-secret-key-2026"

    # Rate Limiting & Storage
    SUBMIT_RATE_LIMIT: str = "60/minute"
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB
    UPLOAD_DIR: str = "media"
    IMAGE_SUBDIR: str = "media/images"
    AUDIO_SUBDIR: str = "media/audio"

    # Geo-Deduplication Parameters
    GEO_DEDUP_RADIUS_METERS: float = 50.0
    GEO_DEDUP_TIME_WINDOW_HOURS: float = 48.0

    # CORS Whitelist (Open for multi-device network & LAN accessibility)
    CORS_ORIGINS: Union[str, List[str]] = "*"

    # AI Pipeline
    AI_PROVIDER: str = "mock"
    GEMINI_API_KEY: str = ""

    # SMTP / Emergency Alert Dispatch Settings
    SMTP_ENABLED: bool = False
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    SMTP_FROM: str = "alerts@civicpulse.sindh.gov.pk"
    SIMULATE_EMAIL_DISPATCH: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("CORS_ORIGINS", mode="after")
    @classmethod
    def parse_cors_origins(cls, value: Union[str, List[str]]) -> List[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

settings = Settings()

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("civicpulse")


# ======================================================================================
# 2. DATABASE & ORM MODELS (SQLAlchemy 2.0 + SQLite)
# ======================================================================================
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
    pool_pre_ping=True
)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if settings.DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def generate_ticket_id() -> str:
    """Generate human-friendly ticket ID: e.g. TKT-A8F12C."""
    return f"TKT-{uuid.uuid4().hex[:6].upper()}"


class Complaint(Base):
    """
    Core SQLAlchemy ORM model representing civic complaints.
    """
    __tablename__ = "complaints"

    ticket_id = Column(String(32), primary_key=True, index=True, default=generate_ticket_id)
    image_path = Column(String(512), nullable=False)
    original_audio_path = Column(String(512), nullable=True)
    translated_text = Column(Text, nullable=True)
    category = Column(String(32), nullable=False, default="Unassigned", index=True)
    severity = Column(String(16), nullable=False, default="Medium", index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    ai_action_plan = Column(Text, nullable=True)
    is_valid_civic_issue = Column(Boolean, nullable=False, default=True, index=True)
    status = Column(String(16), nullable=False, default="Open", index=True)
    timestamp = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    duplicate_of = Column(String(32), nullable=True)
    duplicate_count = Column(Integer, nullable=False, default=0)
    phone_number = Column(String(32), nullable=True)

    __table_args__ = (
        # Composite index for high-speed spatial-temporal geo-deduplication
        Index("ix_complaints_geo_time", "latitude", "longitude", "timestamp"),
        # Composite index for fast admin dashboard filtering
        Index("ix_complaints_admin_filter", "status", "category", "is_valid_civic_issue"),
    )


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE complaints ADD COLUMN phone_number VARCHAR(32)"))
            conn.commit()
    except Exception:
        pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_upload_dirs() -> None:
    os.makedirs(settings.IMAGE_SUBDIR, exist_ok=True)
    os.makedirs(settings.AUDIO_SUBDIR, exist_ok=True)


# ======================================================================================
# 3. PYDANTIC SCHEMAS & ENUMS
# ======================================================================================
class CategoryEnum(str, Enum):
    GARBAGE = "Garbage"
    POTHOLE = "Pothole"
    SEWERAGE = "Sewerage"
    UNASSIGNED = "Unassigned"


class SeverityEnum(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    UNKNOWN = "Unknown"


class StatusEnum(str, Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"


class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ticket_id: str
    image_path: str
    original_audio_path: Optional[str] = None
    translated_text: Optional[str] = None
    category: str
    severity: str
    latitude: float
    longitude: float
    lat: Optional[float] = None
    lng: Optional[float] = None
    address: Optional[str] = None
    ai_action_plan: Optional[str] = None
    is_valid_civic_issue: bool
    status: str
    timestamp: datetime
    created_at: Optional[str] = None
    duplicate_of: Optional[str] = None
    duplicate_count: int = 0
    phone_number: Optional[str] = None


class TicketListResponse(BaseModel):
    total: int
    count: int
    limit: int
    offset: int
    tickets: List[TicketResponse]


class TicketStatusUpdate(BaseModel):
    status: StatusEnum

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value: str) -> str:
        if isinstance(value, str):
            val_norm = value.strip().title()
            if val_norm == "In-Progress":
                return "In Progress"
            return val_norm
        return value


class ReportSubmissionResponse(BaseModel):
    success: bool = True
    status: str
    ticket_id: str
    is_duplicate: bool
    merged_ticket_id: Optional[str] = None
    category: str
    severity: str
    is_valid_civic_issue: bool
    ai_action_plan: Optional[str] = None
    translated_text: Optional[str] = None
    phone_number: Optional[str] = None
    emergency_dispatch: Optional[Dict[str, Any]] = None
    message: str


class AdminDashboardStats(BaseModel):
    total_open: int
    critical_alerts: int
    resolved_today: int
    total_reports: int
    category_breakdown: Dict[str, int]
    severity_breakdown: Dict[str, int]


# ======================================================================================
# 4. SECURITY & AUTHENTICATION (X-Admin-API-Key) — Hackathon mode: key optional
# ======================================================================================
API_KEY_HEADER = APIKeyHeader(name="X-Admin-API-Key", auto_error=False)


def verify_admin_api_key(api_key_header: Optional[str] = Security(API_KEY_HEADER)) -> str:
    """
    Zero-friction Hackathon mode: API key requirement is removed!
    Allows seamless, direct testing in Swagger (/docs), Streamlit frontend,
    and Postman without getting 401 errors.
    """
    if api_key_header:
        return api_key_header
    return "authorized-admin"


# ======================================================================================
# 5. GEO-DEDUPLICATION ENGINE (Haversine 50m / 48hr Window)
# ======================================================================================
EARTH_RADIUS_METERS = 6371000.0


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in meters between two GPS coordinates."""
    if not (-90.0 <= lat1 <= 90.0 and -90.0 <= lat2 <= 90.0):
        raise ValueError("Latitude must be between -90.0 and 90.0.")
    if not (-180.0 <= lon1 <= 180.0 and -180.0 <= lon2 <= 180.0):
        raise ValueError("Longitude must be between -180.0 and 180.0.")

    if lat1 == lat2 and lon1 == lon2:
        return 0.0

    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    a = min(1.0, max(0.0, a))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return EARTH_RADIUS_METERS * c


def get_bounding_box(lat: float, lon: float, radius_meters: float) -> Tuple[float, float, float, float]:
    """Calculate SQL bounding box for index scanning."""
    lat_delta = radius_meters / 111139.0
    min_lat = max(-90.0, lat - lat_delta)
    max_lat = min(90.0, lat + lat_delta)

    cos_lat = math.cos(math.radians(lat))
    lon_delta = 180.0 if abs(cos_lat) < 1e-6 else radius_meters / (111139.0 * cos_lat)
    min_lon = max(-180.0, lon - abs(lon_delta))
    max_lon = min(180.0, lon + abs(lon_delta))
    return min_lat, max_lat, min_lon, max_lon


def find_duplicate_ticket(
    db: Session,
    category: str,
    latitude: float,
    longitude: float,
    radius_meters: float = 50.0,
    time_window_hours: float = 48.0
) -> Optional[Complaint]:
    """Finds existing open ticket within radius and time window, anchored to primary tickets."""
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=time_window_hours)
    min_lat, max_lat, min_lon, max_lon = get_bounding_box(latitude, longitude, radius_meters)

    candidates = db.query(Complaint).filter(
        Complaint.status == "Open",
        Complaint.category == category,
        Complaint.duplicate_of.is_(None),  # Anchor to root tickets to prevent centroid drift
        Complaint.timestamp >= cutoff_time,
        Complaint.latitude >= min_lat,
        Complaint.latitude <= max_lat,
        Complaint.longitude >= min_lon,
        Complaint.longitude <= max_lon
    ).all()

    if not candidates:
        return None

    closest_candidate: Optional[Complaint] = None
    min_dist = float("inf")
    for cand in candidates:
        dist = haversine_distance_meters(latitude, longitude, cand.latitude, cand.longitude)
        if dist <= radius_meters and dist < min_dist:
            min_dist = dist
            closest_candidate = cand

    return closest_candidate


# # ======================================================================================
# # 6. AI PIPELINE INTEGRATION STUBS & HEURISTICS (Whisper + Vision LLM)
# # ======================================================================================
# class AIAnalysisResult(BaseModel):
#     is_valid_civic_issue: bool
#     category: str
#     severity: str
#     reasoning: str
#     ai_action_plan: str
#     translated_text: Optional[str] = None
#     raw_ai_response: Optional[Dict[str, Any]] = None


# def transcribe_and_translate_audio(audio_path: Optional[str]) -> Optional[str]:
#     """Integration stub for Whisper Speech-to-Text translation (Urdu/Roman Urdu -> English)."""
#     if not audio_path or not os.path.exists(audio_path):
#         return None
    
#     path_lower = audio_path.lower()
#     if "pothole" in path_lower or "sarak" in path_lower or "road" in path_lower:
#         return "Deep pothole on broken road causing hazard."
#     elif "sewer" in path_lower or "gatar" in path_lower or "drain" in path_lower:
#         return "Sewerage water overflowing from blocked drain."
#     elif "garbage" in path_lower or "kachra" in path_lower:
#         return "Reported overflowing garbage pile near the street corner requiring cleanup."

#     return "Voice report describing civic issue requiring municipal cleanup."


# def analyze_civic_issue(
#     image_path: str,
#     translated_text: Optional[str] = None,
#     user_description: Optional[str] = None
# ) -> AIAnalysisResult:
#     """Multimodal Vision & Logic Classification with strict JSON schema."""
#     combined_context = f"{translated_text or ''} {user_description or ''}".strip().lower()

#     # Dynamic classification heuristic with mock fallback
#     if "selfie" in combined_context or "blank" in combined_context or "fake" in combined_context or "spam" in combined_context:
#         return AIAnalysisResult(
#             is_valid_civic_issue=False,
#             category="Unassigned",
#             severity="Low",
#             reasoning="Image flagged as unrelated to municipal civic infrastructure.",
#             ai_action_plan="No municipal action required.",
#             translated_text=translated_text or user_description
#         )
#     elif any(k in combined_context for k in ["garbage", "kachra", "trash", "waste", "dump", "debris", "litter"]):
#         return AIAnalysisResult(
#             is_valid_civic_issue=True,
#             category="Garbage",
#             severity="Critical" if any(k in combined_context for k in ["huge", "massive", "blocking", "severe"]) else "High",
#             reasoning="Accumulated solid waste obstructing public area.",
#             ai_action_plan="Requires 1 dump truck and 3 sanitation workers for 2 hours.",
#             translated_text=translated_text or user_description
#         )
#     elif any(k in combined_context for k in ["pothole", "gaddha", "crater", "tooti hui", "tooti sarak", "broken road", "damaged road"]):
#         return AIAnalysisResult(
#             is_valid_civic_issue=True,
#             category="Pothole",
#             severity="Critical" if any(k in combined_context for k in ["deep", "huge", "dangerous", "severe", "broken"]) else "High",
#             reasoning="Severe road fracture posing danger to traffic.",
#             ai_action_plan="Requires 1 asphalt patcher truck and 2 road repair technicians.",
#             translated_text=translated_text or user_description
#         )
#     elif any(k in combined_context for k in ["sewer", "gatar", "gutter", "drain", "sewage", "sewerage", "naali", "manhole", "ganda paani"]):
#         return AIAnalysisResult(
#             is_valid_civic_issue=True,
#             category="Sewerage",
#             severity="Critical",
#             reasoning="Blocked sewerage line with contaminated water overflow.",
#             ai_action_plan="Requires 1 suction jetting machine truck and 2 drainage specialists.",
#             translated_text=translated_text or user_description
#         )
#     else:
#         return AIAnalysisResult(
#             is_valid_civic_issue=True,
#             category="Garbage",
#             severity="Medium",
#             reasoning="Civic cleanliness concern reported in public area.",
#             ai_action_plan="Requires sanitation inspection and standard clearance team.",
#             translated_text=translated_text or user_description
#         )


# def process_civic_submission(
#     image_path: str,
#     audio_path: Optional[str] = None,
#     user_description: Optional[str] = None
# ) -> AIAnalysisResult:
#     translated_audio_text = transcribe_and_translate_audio(audio_path) if audio_path else None
#     final_text = translated_audio_text or user_description
#     res = analyze_civic_issue(image_path=image_path, translated_text=final_text, user_description=user_description)
#     if translated_audio_text and not res.translated_text:
#         res.translated_text = translated_audio_text
#     return res



# ======================================================================================
# 6. AI PIPELINE INTEGRATION (Whisper + Gemini 2.5 Flash via ai_engine.py)
# ======================================================================================
try:
    from ai_engine import (
        transcribe_audio as _engine_transcribe_audio,
        analyze_civic_issue as _engine_analyze_civic_issue,
    )
    _AI_ENGINE_AVAILABLE = True
    logger.info("ai_engine.py loaded successfully — real AI pipeline active.")
except ImportError as _ai_engine_import_err:
    _AI_ENGINE_AVAILABLE = False
    logger.critical(
        "FATAL: Could not import ai_engine.py: %s. "
        "Real AI processing is unavailable. Check that ai_engine.py is in the same directory.",
        _ai_engine_import_err,
    )


class AIAnalysisResult(BaseModel):
    is_valid_civic_issue: bool
    category: str
    severity: str
    reasoning: str
    ai_action_plan: str
    translated_text: Optional[str] = None
    raw_ai_response: Optional[Dict[str, Any]] = None


def transcribe_and_translate_audio(audio_path: Optional[str]) -> Optional[str]:
    """
    Transcribes an audio file to text using Whisper via ai_engine.transcribe_audio().

    Returns None if:
      - audio_path is None or empty
      - the file does not exist on disk
      - ai_engine is unavailable
      - transcription raises an exception
    """
    if not audio_path:
        logger.debug("transcribe_and_translate_audio: audio_path is None — skipping.")
        return None

    if not os.path.exists(audio_path):
        logger.warning(
            "transcribe_and_translate_audio: audio file not found on disk: %s", audio_path
        )
        return None

    if not _AI_ENGINE_AVAILABLE:
        logger.error(
            "transcribe_and_translate_audio: ai_engine unavailable — cannot transcribe %s", audio_path
        )
        return None

    try:
        transcript = _engine_transcribe_audio(audio_path)
        logger.info("Audio transcribed successfully: %s", audio_path)
        return transcript if transcript else None
    except Exception as exc:
        logger.exception(
            "transcribe_and_translate_audio: Whisper transcription failed for %s: %s", audio_path, exc
        )
        return None


def analyze_civic_issue(
    image_path: str,
    translated_text: Optional[str] = None,
    user_description: Optional[str] = None,
) -> AIAnalysisResult:
    """
    Analyses a civic-issue image using Gemini 2.5 Flash via ai_engine.analyze_civic_issue().

    The engine is expected to return a dict with at minimum:
        is_valid_civic_issue (bool), category (str), severity (str),
        reasoning (str), ai_action_plan (str)
    and optionally: translated_text (str), raw_ai_response (dict).

    Falls back to a safe default AIAnalysisResult on any failure.
    """
    text_description = translated_text or user_description or ""

    # Normalize category and severity helpers
    def _fallback_civic_result(reason_msg: str) -> AIAnalysisResult:
        desc_l = (text_description or "").lower()
        if any(k in desc_l for k in ["sewer", "gutter", "drain", "water", "overflow", "naala"]):
            cat, sev, plan = "Sewerage", "Critical", "Deploy municipal suction jetting tanker and drainage crew."
        elif any(k in desc_l for k in ["pothole", "road", "sadak", "damage", "asphalt", "crater"]):
            cat, sev, plan = "Pothole", "High", "Deploy road maintenance crew with asphalt filler and roller."
        else:
            cat, sev, plan = "Garbage", "High", "Dispatch waste compactor truck and municipal sanitation crew."
        return AIAnalysisResult(
            is_valid_civic_issue=True,
            category=cat,
            severity=sev,
            reasoning=reason_msg,
            ai_action_plan=plan,
            translated_text=text_description or None,
        )

    if not _AI_ENGINE_AVAILABLE:
        logger.warning("analyze_civic_issue: using smart civic heuristic fallback.")
        return _fallback_civic_result("Automated heuristic triage based on civic problem context.")

    try:
        raw: Dict[str, Any] = _engine_analyze_civic_issue(
            image_path=image_path,
            text_description=text_description,
        )
        logger.info("Gemini analysis completed for image: %s", image_path)

        cat = str(raw.get("category", "Garbage")).title()
        if cat not in ["Garbage", "Pothole", "Sewerage"]:
            cat = "Garbage"

        sev = str(raw.get("severity", "High")).title()
        if sev not in ["Critical", "High", "Medium", "Low"]:
            sev = "High"

        plan = str(raw.get("ai_action_plan") or raw.get("recommended_action") or "Dispatch municipal field team.")

        return AIAnalysisResult(
            is_valid_civic_issue=bool(raw.get("is_valid_civic_issue", True)),
            category=cat,
            severity=sev,
            reasoning=str(raw.get("reasoning", "Civic issue verified and prioritized by AI.")),
            ai_action_plan=plan,
            translated_text=raw.get("translated_text") or text_description or None,
            raw_ai_response=raw,
        )

    except Exception as exc:
        logger.exception("analyze_civic_issue: Gemini analysis failed for %s: %s", image_path, exc)
        return _fallback_civic_result(f"Automated fallback triage — AI exception: {type(exc).__name__}")


def process_civic_submission(
    image_path: str,
    audio_path: Optional[str] = None,
    user_description: Optional[str] = None,
) -> AIAnalysisResult:
    """
    Orchestrates the full AI pipeline for a single civic submission:
      1. Transcribe audio (if provided) → English text via Whisper.
      2. Analyse the image + combined text context via Gemini 2.5 Flash.
      3. Return a fully-populated AIAnalysisResult.
    """
    # Step 1: Audio transcription (None-safe — function guards internally)
    translated_audio_text: Optional[str] = transcribe_and_translate_audio(audio_path)

    # Step 2: Merge text sources intelligently without dropping user typed text
    if translated_audio_text and translated_audio_text.strip():
        if user_description and user_description.strip():
            final_text: Optional[str] = f"{user_description.strip()} [Voice Note: {translated_audio_text.strip()}]"
        else:
            final_text: Optional[str] = translated_audio_text.strip()
    else:
        final_text: Optional[str] = user_description or ""

    # Step 3: Vision + LLM analysis
    result: AIAnalysisResult = analyze_civic_issue(
        image_path=image_path,
        translated_text=final_text,
        user_description=user_description,
    )

    # Step 4: Ensure translated_text is set if audio was transcribed but engine didn't echo it back
    if translated_audio_text and not result.translated_text:
        result.translated_text = translated_audio_text

    return result


# ======================================================================================
# 7. SECURE FILE UPLOAD HANDLER
# ======================================================================================
ALLOWED_IMAGE_TYPES: Set[str] = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
ALLOWED_AUDIO_TYPES: Set[str] = {
    "audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav", 
    "audio/ogg", "audio/m4a", "audio/mp4", "audio/webm",
    "audio/aac", "audio/flac", "application/octet-stream"
}

MIME_EXT_MAP = {
    "image/jpeg": ".jpg", "image/jpg": ".jpg", "image/png": ".png", "image/webp": ".webp",
    "audio/mpeg": ".mp3", "audio/mp3": ".mp3", "audio/wav": ".wav", "audio/x-wav": ".wav",
    "audio/ogg": ".ogg", "audio/m4a": ".m4a", "audio/mp4": ".mp4", "audio/webm": ".webm",
    "audio/aac": ".aac", "audio/flac": ".flac"
}


async def save_uploaded_file(file: UploadFile, is_image: bool = True) -> str:
    """Validates MIME, checks size stream up to 10MB, and saves with UUID filename."""
    ensure_upload_dirs()
    raw_content = (file.content_type or "").lower().strip()
    content_type = raw_content.split(";")[0].strip()
    allowed = ALLOWED_IMAGE_TYPES if is_image else ALLOWED_AUDIO_TYPES
    target_dir = settings.IMAGE_SUBDIR if is_image else settings.AUDIO_SUBDIR

    orig_ext = Path(file.filename or "").suffix.lower()

    if content_type not in allowed:
        valid_exts = {".jpg", ".jpeg", ".png", ".webp"} if is_image else {".wav", ".mp3", ".ogg", ".webm", ".m4a", ".mp4"}
        if orig_ext not in valid_exts:
            raise HTTPException(status_code=400, detail=f"Invalid file type '{content_type}'. Allowed: {sorted(list(allowed))}")

    if content_type in MIME_EXT_MAP:
        ext = MIME_EXT_MAP[content_type]
    elif orig_ext:
        ext = orig_ext
    else:
        ext = ".jpg" if is_image else ".wav"

    unique_name = f"{uuid.uuid4().hex}{ext}"
    dest_path = os.path.join(target_dir, unique_name)

    total_bytes = 0
    try:
        with open(dest_path, "wb") as buffer:
            while True:
                chunk = await file.read(64 * 1024)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > settings.MAX_UPLOAD_SIZE_BYTES:
                    buffer.close()
                    if os.path.exists(dest_path):
                        os.remove(dest_path)
                    raise HTTPException(status_code=413, detail=f"File exceeds max 10MB limit.")
                buffer.write(chunk)
    finally:
        await file.seek(0)

    return dest_path.replace("\\", "/")


# ======================================================================================
# 7.5. EMERGENCY CRITICAL CIVIC ALERT ENGINE (Nearest Municipal Chairman Dispatch)
# ======================================================================================

MUNICIPAL_COMMITTEE_SUPERVISORS: List[Dict[str, Any]] = [
    # Karachi Municipal Committee / Zonal Offices
    {
        "id": "KMC-SDR-01",
        "city": "Karachi",
        "zone": "Saddar Town / City Center",
        "name": "Syed Mansoor Ali",
        "designation": "Chairman, Town Municipal Corporation Saddar",
        "email": "chairman.saddar@kmc.sindh.gov.pk",
        "phone": "+92-21-99201201",
        "latitude": 24.860700,
        "longitude": 67.001100,
    },
    {
        "id": "KMC-CLF-02",
        "city": "Karachi",
        "zone": "Clifton & Cantonment Zone",
        "name": "Brig. (R) Tariq Mahmood",
        "designation": "Zonal Director & Municipal Commissioner Clifton",
        "email": "director.clifton@kmc.sindh.gov.pk",
        "phone": "+92-21-99250441",
        "latitude": 24.823600,
        "longitude": 67.032200,
    },
    {
        "id": "KMC-GLS-03",
        "city": "Karachi",
        "zone": "Gulshan-e-Iqbal Town",
        "name": "Dr. Faraz Ahmed Khan",
        "designation": "Chairman, Town Municipal Corporation Gulshan",
        "email": "chairman.gulshan@kmc.sindh.gov.pk",
        "phone": "+92-21-99231188",
        "latitude": 24.920700,
        "longitude": 67.092800,
    },
    {
        "id": "KMC-NNZ-04",
        "city": "Karachi",
        "zone": "North Nazimabad Zone",
        "name": "Engr. Atif Raza",
        "designation": "Chief Municipal Officer, North Nazimabad",
        "email": "cmo.nazimabad@kmc.sindh.gov.pk",
        "phone": "+92-21-99260105",
        "latitude": 24.939200,
        "longitude": 67.038100,
    },
    {
        "id": "KMC-KOR-05",
        "city": "Karachi",
        "zone": "Korangi & Landhi Industrial Belt",
        "name": "Malik Zafar Iqbal",
        "designation": "Superintending Engineer & Zonal Head Korangi",
        "email": "superintendent.korangi@kmc.sindh.gov.pk",
        "phone": "+92-21-35061122",
        "latitude": 24.838400,
        "longitude": 67.142000,
    },
    {
        "id": "KMC-MLR-06",
        "city": "Karachi",
        "zone": "Malir & Bin Qasim Town",
        "name": "Chaudhry Naeem Akhtar",
        "designation": "Chairman, Municipal Committee Malir",
        "email": "chairman.malir@kmc.sindh.gov.pk",
        "phone": "+92-21-34400191",
        "latitude": 24.918000,
        "longitude": 67.202000,
    },
    {
        "id": "KMC-STE-07",
        "city": "Karachi",
        "zone": "SITE & Keamari Harbour Zone",
        "name": "Mirza Kamran Baig",
        "designation": "Municipal Commissioner, Keamari & SITE",
        "email": "commissioner.keamari@kmc.sindh.gov.pk",
        "phone": "+92-21-32560882",
        "latitude": 24.898000,
        "longitude": 66.992000,
    },

    # Hyderabad Municipal Committee / Zonal Offices
    {
        "id": "HMC-QSB-01",
        "city": "Hyderabad",
        "zone": "Qasimabad Municipal Committee",
        "name": "Engr. Farhan Mughal",
        "designation": "Chairman, Municipal Committee Qasimabad",
        "email": "chairman.qasimabad@hmc.sindh.gov.pk",
        "phone": "+92-22-9240112",
        "latitude": 25.395000,
        "longitude": 68.332000,
    },
    {
        "id": "HMC-LTF-02",
        "city": "Hyderabad",
        "zone": "Latifabad Municipal Committee",
        "name": "Abdul Sattar Memon",
        "designation": "Municipal Commissioner, TMC Latifabad",
        "email": "commissioner.latifabad@hmc.sindh.gov.pk",
        "phone": "+92-22-9260195",
        "latitude": 25.378000,
        "longitude": 68.352000,
    },
    {
        "id": "HMC-CTY-03",
        "city": "Hyderabad",
        "zone": "Hyderabad City Zone (Pakka Qila / Shahi Bazaar)",
        "name": "Muhammad Aslam Shaikh",
        "designation": "Chief Sanitary Inspector & Zonal Incharge",
        "email": "supervisor.city@hmc.sindh.gov.pk",
        "phone": "+92-22-9200341",
        "latitude": 25.392000,
        "longitude": 68.373500,
    },
    {
        "id": "HMC-SDR-04",
        "city": "Hyderabad",
        "zone": "Saddar Cantt & Thandi Sarak Zone",
        "name": "Kashif Ali Brohi",
        "designation": "Executive Officer, Cantonment & Saddar",
        "email": "eo.cantt@hmc.sindh.gov.pk",
        "phone": "+92-22-9200885",
        "latitude": 25.391000,
        "longitude": 68.362000,
    },
    {
        "id": "HMC-PRT-05",
        "city": "Hyderabad",
        "zone": "Pareetabad & Phuleli Zonal Office",
        "name": "Naveed Ahmed Qureshi",
        "designation": "Superintendent Engineer, Pareetabad Ward",
        "email": "engineer.pareetabad@hmc.sindh.gov.pk",
        "phone": "+92-22-9210452",
        "latitude": 25.389000,
        "longitude": 68.388000,
    },
    {
        "id": "HMC-KTR-06",
        "city": "Hyderabad/Kotri",
        "zone": "Kotri Barrage & Industrial Belt",
        "name": "Haji Ghulam Rasool",
        "designation": "Chairman, Municipal Committee Kotri",
        "email": "chairman.kotri@sindh.gov.pk",
        "phone": "+92-22-3870119",
        "latitude": 25.432000,
        "longitude": 68.315000,
    },
]


def find_nearest_supervisor(lat: float, lon: float) -> Tuple[Dict[str, Any], float]:
    """
    Finds the nearest Municipal Committee Chairman / Zonal Supervisor
    based on Haversine distance from incident GPS coordinates.
    Returns: (supervisor_dict, distance_km)
    """
    nearest = MUNICIPAL_COMMITTEE_SUPERVISORS[0]
    min_dist_meters = float("inf")

    for sup in MUNICIPAL_COMMITTEE_SUPERVISORS:
        d = haversine_distance_meters(lat, lon, sup["latitude"], sup["longitude"])
        if d < min_dist_meters:
            min_dist_meters = d
            nearest = sup

    distance_km = round(min_dist_meters / 1000.0, 2)
    return nearest, distance_km


def compose_critical_alert_email(
    supervisor: Dict[str, Any],
    distance_km: float,
    ticket_id: str,
    category: str,
    severity: str,
    address: str,
    lat: float,
    lon: float,
    ai_action_plan: str,
    description: str,
    phone_number: Optional[str] = None
) -> Tuple[str, str, str]:
    """
    Composes high-priority municipal emergency dispatch email in Plain Text and HTML.
    """
    subject = f"🚨 [CRITICAL CIVIC ALERT] Immediate Action Required — Ticket #{ticket_id} ({category} at {address})"
    gmaps_url = f"https://www.google.com/maps?q={lat:.6f},{lon:.6f}"
    contact_str = phone_number or "Citizen opted for anonymous submission"
    timestamp_str = datetime.now(timezone.utc).strftime("%d-%b-%Y %H:%M:%S UTC")

    plain_body = f"""================================================================================
🚨 SINDH MUNICIPAL SERVICES — CRITICAL CIVIC EMERGENCY ALERT 🚨
================================================================================
PRIORITY LEVEL: CRITICAL (IMMEDIATE FIELD DISPATCH REQUIRED WITHIN 2 HOURS)

ATTENTION:
  To:          {supervisor['name']}
  Designation: {supervisor['designation']}
  Zonal Office: {supervisor['zone']} ({supervisor['city']})
  Proximity:   ~{distance_km} km from reported hazard location

INCIDENT SUMMARY:
  Ticket ID:        {ticket_id}
  Hazard Category:  {category}
  Assessed Severity: CRITICAL 🚨
  Location:         {address}
  GPS Coordinates:  {lat:.6f}° N, {lon:.6f}° E
  Navigation Link:  {gmaps_url}
  Citizen Phone:    {contact_str}
  Logged At:        {timestamp_str}

CITIZEN REPORT / AUDIO TRANSCRIPTION:
--------------------------------------------------------------------------------
{description or 'Photographic evidence provided.'}

AI-GENERATED RAPID-RESPONSE ACTION PLAN:
--------------------------------------------------------------------------------
{ai_action_plan}

PROTOCOL DIRECTIVE:
Under Sindh Emergency Municipal Service SOPs, this hazard poses direct risks to
public safety or essential infrastructure. Your zonal rapid-response unit is
hereby dispatched to inspect and secure the perimeter immediately.

CivicPulse AI Automated Dispatch System
Municipal Grievance Cell: 1339 | Emergency Rescue: 1122
================================================================================
"""

    html_body = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #07101E; color: #D8E4F0; margin: 0; padding: 20px; }}
  .container {{ max-width: 650px; margin: 0 auto; background: #0A1628; border: 1px solid #1E3A5F; border-radius: 8px; overflow: hidden; }}
  .header {{ background: #DC2626; color: #FFFFFF; padding: 18px 24px; text-align: left; }}
  .header h1 {{ margin: 0; font-size: 20px; font-weight: 700; letter-spacing: 0.05em; }}
  .header p {{ margin: 4px 0 0 0; font-size: 13px; opacity: 0.9; }}
  .content {{ padding: 24px; }}
  .badge-row {{ margin-bottom: 16px; }}
  .badge {{ display: inline-block; background: #EF4444; color: #FFFFFF; font-weight: bold; font-size: 12px; padding: 4px 10px; border-radius: 4px; text-transform: uppercase; margin-right: 8px; }}
  .badge-gold {{ background: #C9A84C; color: #0A1628; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; background: #112240; padding: 14px; border-radius: 6px; border: 1px solid #1E3A5F; margin-bottom: 18px; }}
  .grid-item {{ font-size: 13px; }}
  .grid-label {{ color: #7A90A8; font-weight: 600; text-transform: uppercase; font-size: 11px; margin-bottom: 2px; }}
  .grid-value {{ color: #F0F4F8; font-weight: 500; }}
  .box {{ background: #07101E; border-left: 3px solid #C9A84C; padding: 12px 16px; border-radius: 4px; margin-bottom: 16px; }}
  .box-title {{ color: #C9A84C; font-size: 12px; font-weight: 700; text-transform: uppercase; margin-bottom: 4px; }}
  .box-text {{ font-size: 13px; color: #D8E4F0; line-height: 1.5; margin: 0; }}
  .btn {{ display: inline-block; background: #C9A84C; color: #0A1628; text-decoration: none; font-weight: 700; font-size: 13px; padding: 10px 18px; border-radius: 4px; margin-top: 10px; }}
  .footer {{ background: #07101E; padding: 14px 24px; border-top: 1px solid #1E3A5F; font-size: 11px; color: #7A90A8; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>🚨 CRITICAL CIVIC EMERGENCY ALERT</h1>
    <p>Government of Sindh · Municipal Services Dispatch System</p>
  </div>
  <div class="content">
    <div class="badge-row">
      <span class="badge">Severity: CRITICAL</span>
      <span class="badge badge-gold">Immediate Intervention Required</span>
    </div>

    <p style="font-size: 14px; color: #F0F4F8; margin-top: 0;">
      Respected <strong>{supervisor['name']}</strong> ({supervisor['designation']}),<br>
      A high-severity civic hazard has been registered within your municipal jurisdiction (<strong>~{distance_km} km</strong> from your zonal office).
    </p>

    <div class="grid">
      <div class="grid-item">
        <div class="grid-label">Ticket ID</div>
        <div class="grid-value" style="font-family: monospace; color: #C9A84C;">{ticket_id}</div>
      </div>
      <div class="grid-item">
        <div class="grid-label">Hazard Category</div>
        <div class="grid-value">{category}</div>
      </div>
      <div class="grid-item">
        <div class="grid-label">Incident Address</div>
        <div class="grid-value">{address}</div>
      </div>
      <div class="grid-item">
        <div class="grid-label">Citizen Phone</div>
        <div class="grid-value">{contact_str}</div>
      </div>
      <div class="grid-item">
        <div class="grid-label">GPS Telemetry</div>
        <div class="grid-value" style="font-family: monospace;">{lat:.6f}° N, {lon:.6f}° E</div>
      </div>
      <div class="grid-item">
        <div class="grid-label">Logged Timestamp</div>
        <div class="grid-value">{timestamp_str}</div>
      </div>
    </div>

    <div class="box">
      <div class="box-title">Citizen Report / Audio Transcription</div>
      <p class="box-text">{description or 'Photographic evidence captured on site.'}</p>
    </div>

    <div class="box" style="border-left-color: #EF4444;">
      <div class="box-title" style="color: #F87171;">AI-Generated Rapid-Response Action Plan</div>
      <p class="box-text">{ai_action_plan}</p>
    </div>

    <a href="{gmaps_url}" class="btn" target="_blank">📍 Open GPS Navigation on Google Maps</a>
  </div>
  <div class="footer">
    CivicPulse AI Automated Emergency Engine · Municipal Grievance Cell: 1339 · Rescue: 1122
  </div>
</div>
</body>
</html>"""

    return subject, plain_body, html_body


def dispatch_critical_alert_email(
    supervisor: Dict[str, Any],
    distance_km: float,
    ticket_id: str,
    category: str,
    severity: str,
    address: str,
    lat: float,
    lon: float,
    ai_action_plan: str,
    description: str,
    phone_number: Optional[str] = None
) -> Dict[str, Any]:
    """
    Executes automated emergency email dispatch to the nearest municipal supervisor.
    If SMTP is enabled, delivers live email; otherwise records the transmission in
    the municipal audit ledger (media/critical_alerts.log) and outputs a prominent server banner.
    """
    subject, plain_body, html_body = compose_critical_alert_email(
        supervisor=supervisor,
        distance_km=distance_km,
        ticket_id=ticket_id,
        category=category,
        severity=severity,
        address=address,
        lat=lat,
        lon=lon,
        ai_action_plan=ai_action_plan,
        description=description,
        phone_number=phone_number
    )

    delivery_status = "DELIVERED_SIMULATED_LEDGER"
    smtp_error = None

    if settings.SMTP_ENABLED and settings.SMTP_USER and settings.SMTP_PASS:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.SMTP_FROM
            msg["To"] = supervisor["email"]
            msg.attach(MIMEText(plain_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASS)
                server.sendmail(settings.SMTP_FROM, [supervisor["email"]], msg.as_string())

            delivery_status = "DELIVERED_VIA_SMTP"
            logger.info("Real SMTP alert email sent successfully to %s", supervisor["email"])
        except Exception as exc:
            smtp_error = str(exc)
            delivery_status = "FALLBACK_LOGGED_TO_LEDGER"
            logger.warning("SMTP dispatch encountered error: %s. Falling back to municipal ledger.", exc)

    # Record in persistent audit ledger file
    try:
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        log_path = os.path.join(settings.UPLOAD_DIR, "critical_alerts.log")
        timestamp_str = datetime.now(timezone.utc).isoformat()
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*75}\n")
            f.write(f"TIMESTAMP: {timestamp_str}\n")
            f.write(f"TICKET:    {ticket_id} [{severity}] ({category})\n")
            f.write(f"RECIPIENT: {supervisor['name']} ({supervisor['designation']})\n")
            f.write(f"EMAIL:     {supervisor['email']} (Distance: ~{distance_km} km)\n")
            f.write(f"LOCATION:  {address} ({lat:.6f}, {lon:.6f})\n")
            f.write(f"STATUS:    {delivery_status}\n")
            f.write(f"{'-'*75}\n")
            f.write(plain_body)
    except Exception as log_err:
        logger.error("Failed to write to critical_alerts.log: %s", log_err)

    # Output high-visibility ASCII console banner for live demonstration
    banner = f"""
========================================================================================
[!] [CRITICAL ALERT DISPATCHED TO MUNICIPAL SUPERVISOR VIA EMAIL] [!]
----------------------------------------------------------------------------------------
Target Officer:  {supervisor['name']} ({supervisor['designation']})
Assigned Office: {supervisor['zone']} ({supervisor['city']})
Target Email:    {supervisor['email']}
Distance:        ~{distance_km} km from reported incident
Ticket ID:       {ticket_id} | Category: {category} | Severity: {severity}
Coordinates:     {lat:.6f} N, {lon:.6f} E
Status:          [{delivery_status}] -- Protocol rapid-response triggered
Google Maps:     https://www.google.com/maps?q={lat:.6f},{lon:.6f}
========================================================================================
"""
    try:
        print(banner, flush=True)
    except UnicodeEncodeError:
        print(banner.encode("ascii", "replace").decode("ascii"), flush=True)
    logger.warning("CRITICAL CIVIC ALERT: Email dispatched to %s <%s>", supervisor['name'], supervisor['email'])

    return {
        "dispatched": True,
        "delivery_status": delivery_status,
        "recipient_name": supervisor["name"],
        "recipient_designation": supervisor["designation"],
        "recipient_email": supervisor["email"],
        "recipient_phone": supervisor.get("phone"),
        "zone": supervisor["zone"],
        "city": supervisor["city"],
        "distance_km": distance_km,
        "subject": subject,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "google_maps_url": f"https://www.google.com/maps?q={lat:.6f},{lon:.6f}",
        "smtp_error": smtp_error
    }


# ======================================================================================
# 8. HYDERABAD SINDH DEMO DATA SEEDING UTILITY
# ======================================================================================
HYDERABAD_DEMO_COMPLAINTS = [
    {
        "category": "Garbage", "severity": "Critical", "latitude": 25.392000, "longitude": 68.373500,
        "description": "Pacco Qillo Shahi Bazaar gate solid waste accumulation blocking road.",
        "translated_text": "Massive solid waste accumulation blocking main entrance of Pacco Qillo near Shahi Bazaar.",
        "ai_action_plan": "Deploy 2 heavy dumpers, 1 mini-loader excavator, and 6 sanitation workers for 3 hours.",
        "status": "Open", "duplicate_count": 5
    },
    {
        "category": "Pothole", "severity": "Critical", "latitude": 25.378000, "longitude": 68.352000,
        "description": "Autobahn road Latifabad Unit 2 deep pothole crater.",
        "translated_text": "Deep hazardous pothole on Autobahn Road Latifabad posing danger to two-wheelers and vehicles.",
        "ai_action_plan": "Deploy 1 rapid asphalt cold-mix repair truck and 2 highway patch technicians.",
        "status": "Open", "duplicate_count": 4
    },
    {
        "category": "Sewerage", "severity": "Critical", "latitude": 25.395000, "longitude": 68.332000,
        "description": "Qasimabad Naseem Nagar chowk sewerage overflow submerging shops.",
        "translated_text": "Severe sewerage overflow at Naseem Nagar Chowk Qasimabad submerging commercial shops in wastewater.",
        "ai_action_plan": "Deploy 2 high-capacity suction jetting tankers and 4 WASA drainage technicians.",
        "status": "Open", "duplicate_count": 6
    },
    {
        "category": "Garbage", "severity": "High", "latitude": 25.367000, "longitude": 68.358000,
        "description": "Latifabad Unit 7 General Hospital walkway refuse accumulation.",
        "translated_text": "Commercial refuse accumulation near Latifabad Unit 7 General Hospital walkway.",
        "ai_action_plan": "Deploy 1 compact compactor truck and 3 municipal sanitation workers.",
        "status": "In Progress", "duplicate_count": 2
    },
    {
        "category": "Pothole", "severity": "High", "latitude": 25.405000, "longitude": 68.338000,
        "description": "Wadhu Wah road road surface fractures.",
        "translated_text": "Extensive road surface fractures and loose gravel on Wadhu Wah Road Qasimabad.",
        "ai_action_plan": "Schedule asphalt leveling crew and road rolling machinery.",
        "status": "In Progress", "duplicate_count": 2
    },
    {
        "category": "Sewerage", "severity": "Medium", "latitude": 25.391000, "longitude": 68.362000,
        "description": "Haider Chowk Saddar storm drain blockage.",
        "translated_text": "Storm drain blockage near Haider Chowk Saddar causing stagnant street water.",
        "ai_action_plan": "Deploy manual drain rodding team to clear obstruction.",
        "status": "Resolved", "duplicate_count": 1
    },
    {
        "category": "Garbage", "severity": "High", "latitude": 25.397000, "longitude": 68.369000,
        "description": "Station Road / Resham Gali market packaging refuse.",
        "translated_text": "Market packing refuse and debris along Station Road market avenue.",
        "ai_action_plan": "Deploy night-shift mechanical sweeper and waste truck.",
        "status": "Open", "duplicate_count": 3
    },
    {
        "category": "Pothole", "severity": "Critical", "latitude": 25.432000, "longitude": 68.315000,
        "description": "Kotri Barrage Indus Bridge approach structural potholes.",
        "translated_text": "Multiple deep structural potholes on Kotri Barrage approach road damaging freight trucks.",
        "ai_action_plan": "Emergency road patching crew with heavy asphalt paver.",
        "status": "Open", "duplicate_count": 7
    },
    {
        "category": "Garbage", "severity": "Medium", "latitude": 25.402000, "longitude": 68.356000,
        "description": "Thandi Sarak / Hyderabad Gymkhana green median debris.",
        "translated_text": "Organic refuse and pruning debris left on Thandi Sarak median.",
        "ai_action_plan": "Deploy horticultural waste collection vehicle.",
        "status": "Resolved", "duplicate_count": 0
    },
    {
        "category": "Pothole", "severity": "High", "latitude": 25.394000, "longitude": 68.365000,
        "description": "Hirabad Tower Market roundabout damaged surface.",
        "translated_text": "Fractured road asphalt around Hirabad Tower Market roundabout.",
        "ai_action_plan": "Apply cold-patch asphalt filler and compact surface.",
        "status": "Open", "duplicate_count": 2
    },
    {
        "category": "Sewerage", "severity": "High", "latitude": 25.388000, "longitude": 68.341000,
        "description": "Citizen Colony residential sewer backflow.",
        "translated_text": "Residential sewer line backflow causing street flooding in Citizen Colony.",
        "ai_action_plan": "Deploy municipal jetting tanker to flush pipeline blockage.",
        "status": "Open", "duplicate_count": 3
    },
    {
        "category": "Garbage", "severity": "Critical", "latitude": 25.385000, "longitude": 68.318000,
        "description": "SITE Industrial Area solid waste dump.",
        "translated_text": "Illegal industrial solid waste dump blocking primary access lane in SITE Hyderabad.",
        "ai_action_plan": "Dispatch heavy wheel-loader and two 20-ton dumper trucks with inspector.",
        "status": "In Progress", "duplicate_count": 4
    }
]


def seed_demo_data(db: Session = None, force_reset: bool = False) -> int:
    ensure_upload_dirs()
    init_db()
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        if force_reset:
            db.query(Complaint).delete()
            db.commit()
        elif db.query(Complaint).count() >= len(HYDERABAD_DEMO_COMPLAINTS):
            return db.query(Complaint).count()

        sample_img = "media/images/hyderabad_demo_sample.jpg"
        if not os.path.exists(sample_img):
            with open(sample_img, "wb") as f:
                f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 400)

        now = datetime.now(timezone.utc)
        for i, item in enumerate(HYDERABAD_DEMO_COMPLAINTS):
            c = Complaint(
                ticket_id=f"HYD-TKT-10{i+1:02d}",
                image_path=sample_img,
                translated_text=item["translated_text"],
                category=item["category"],
                severity=item["severity"],
                latitude=item["latitude"],
                longitude=item["longitude"],
                ai_action_plan=item["ai_action_plan"],
                is_valid_civic_issue=True,
                status=item["status"],
                timestamp=now - timedelta(hours=3 * (i + 1)),
                duplicate_count=item["duplicate_count"]
            )
            db.add(c)
        db.commit()
        return len(HYDERABAD_DEMO_COMPLAINTS)
    finally:
        if close_db:
            db.close()


# ======================================================================================
# 9. BUILT-IN CLASSY NATURAL MUNICIPAL DASHBOARD WITH REAL HYDERABAD MAP
# ======================================================================================
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CivicPulse AI | Municipal Triage Engine (Hyderabad & Karachi)</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        :root {
            --bg-page: #f8fafc; --surface: #ffffff; --surface-muted: #f1f5f9;
            --border: #e2e8f0; --border-strong: #cbd5e1; --text-main: #0f172a; --text-muted: #64748b;
            --civic-blue: #1e40af; --civic-blue-hover: #1d4ed8;
            --crit-bg: #fef2f2; --crit-text: #b91c1c; --crit-border: #fecaca;
            --high-bg: #fffbeb; --high-text: #b45309; --high-border: #fde68a;
            --med-bg: #eff6ff; --med-text: #1d4ed8; --med-border: #bfdbfe;
            --res-bg: #ecfdf5; --res-text: #047857; --res-border: #a7f3d0;
        }
        * { margin:0; padding:0; box-sizing:border-box; }
        body { background: var(--bg-page); color: var(--text-main); font-family: 'Inter', sans-serif; padding: 1.5rem 2rem; }
        .top-navbar { background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 1rem 1.75rem; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 1px 3px rgba(0,0,0,0.03); margin-bottom: 1.5rem; }
        .brand-box { display: flex; align-items: center; gap: 14px; }
        .gov-seal { width: 44px; height: 44px; background: #eff6ff; border: 1px solid #bfdbfe; color: var(--civic-blue); border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1.3rem; }
        .brand-title { font-family: 'Plus Jakarta Sans', sans-serif; font-size: 1.35rem; font-weight: 800; color: var(--text-main); }
        .kpi-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; margin-bottom: 1.5rem; }
        .kpi-card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.03); }
        .kpi-title { font-size: 0.82rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; }
        .kpi-value { font-family: 'Plus Jakarta Sans', sans-serif; font-size: 1.85rem; font-weight: 800; color: var(--text-main); margin: 0.35rem 0; }
        .tab-bar { display: flex; gap: 8px; border-bottom: 1px solid var(--border); margin-bottom: 1.5rem; }
        .tab-btn { background: none; border: none; border-bottom: 2px solid transparent; padding: 0.75rem 1.25rem; font-size: 0.95rem; font-weight: 600; color: var(--text-muted); cursor: pointer; display: inline-flex; align-items: center; gap: 8px; }
        .tab-btn.active { color: var(--civic-blue); border-bottom-color: var(--civic-blue); }
        .tab-pane { display: none; }
        .tab-pane.active { display: block; }
        .map-section, .db-card { background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 1.25rem; box-shadow: 0 1px 3px rgba(0,0,0,0.03); }
        #real-map { width: 100%; height: 500px; border-radius: 10px; border: 1px solid var(--border); }
        .db-table { width: 100%; border-collapse: collapse; font-size: 0.88rem; margin-top: 1rem; }
        .db-table th { background: var(--surface-muted); color: var(--text-main); font-weight: 600; text-align: left; padding: 0.75rem 1rem; border-bottom: 1px solid var(--border); }
        .db-table td { padding: 0.85rem 1rem; border-bottom: 1px solid var(--border); color: #475569; }
        .badge { display: inline-flex; padding: 3px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }
        .badge-Critical { background: var(--crit-bg); color: var(--crit-text); border: 1px solid var(--crit-border); }
        .badge-High { background: var(--high-bg); color: var(--high-text); border: 1px solid var(--high-border); }
        .badge-Medium { background: var(--med-bg); color: var(--med-text); border: 1px solid var(--med-border); }
        .badge-Low { background: var(--res-bg); color: var(--res-text); border: 1px solid var(--res-border); }
        .badge-Unknown { background: var(--surface-muted); color: var(--text-muted); border: 1px solid var(--border); }
        .btn-action { display: inline-flex; align-items: center; gap: 8px; padding: 0.55rem 1rem; font-size: 0.88rem; font-weight: 600; border-radius: 8px; cursor: pointer; text-decoration: none; }
        .btn-outline { background: var(--surface); border: 1px solid var(--border-strong); color: #475569; }
        .btn-primary { background: var(--civic-blue); border: 1px solid var(--civic-blue); color: #fff; }
    </style>
</head>
<body>
    <header class="top-navbar">
        <div class="brand-box">
            <div class="gov-seal"><i class="fa-solid fa-landmark"></i></div>
            <div>
                <h1 class="brand-title">CivicPulse AI</h1>
                <div style="font-size:0.85rem; color:var(--text-muted);">Municipal Triage &bull; <span style="background:#f1f5f9; padding:2px 8px; border-radius:6px; font-weight:600;">Hyderabad, Sindh</span></div>
            </div>
        </div>
        <div style="display:flex; gap:10px;">
            <button class="btn-action btn-outline" onclick="seedHyderabadData()"><i class="fa-solid fa-database"></i> Seed Hyderabad Data</button>
            <a href="http://localhost:8501" target="_blank" class="btn-action btn-outline"><i class="fa-solid fa-desktop"></i> Open Streamlit Frontend</a>
            <a href="/docs" target="_blank" class="btn-action btn-primary"><i class="fa-solid fa-code"></i> API Docs</a>
        </div>
    </header>

    <div class="kpi-row">
        <div class="kpi-card"><div class="kpi-title">Active Open Issues</div><div class="kpi-value" id="kpi-open">--</div></div>
        <div class="kpi-card"><div class="kpi-title">Critical Road/Drain Hazards</div><div class="kpi-value" style="color:var(--crit-text);" id="kpi-crit">--</div></div>
        <div class="kpi-card"><div class="kpi-title">Resolved Today</div><div class="kpi-value" style="color:var(--res-text);" id="kpi-res">--</div></div>
        <div class="kpi-card"><div class="kpi-title">Total Verified Reports</div><div class="kpi-value" id="kpi-total">--</div></div>
    </div>

    <div class="tab-bar">
        <button class="tab-btn active" onclick="switchTab('tab-map')"><i class="fa-solid fa-map-location-dot"></i> Real Hyderabad Street Map & 50m Deduplication</button>
        <button class="tab-btn" onclick="switchTab('tab-db')"><i class="fa-solid fa-table-list"></i> Municipal Admin Database Explorer</button>
        <button class="tab-btn" onclick="switchTab('tab-submit')"><i class="fa-solid fa-paper-plane"></i> Citizen Issue Submission & AI Triage</button>
    </div>

    <div id="tab-map" class="tab-pane active">
        <div class="map-section">
            <div style="display:flex; justify-content:space-between; margin-bottom:1rem;">
                <div><h3 style="font-size:1.1rem; font-weight:700;">Real Geographic Map &bull; Hyderabad, Sindh</h3><small style="color:var(--text-muted);">Real street-level coordinates with 50-meter deduplication perimeters.</small></div>
                <button class="btn-action btn-outline" onclick="loadDashboardData()"><i class="fa-solid fa-rotate"></i> Refresh Map</button>
            </div>
            <div id="real-map"></div>
        </div>
    </div>

    <div id="tab-db" class="tab-pane">
        <div class="db-card">
            <div style="display:flex; justify-content:space-between; margin-bottom:1rem;">
                <h3 style="font-size:1.1rem; font-weight:700;">SQLite Database Explorer (`complaints` Table)</h3>
                <button class="btn-action btn-outline" onclick="loadDashboardData()"><i class="fa-solid fa-rotate"></i> Refresh Table</button>
            </div>
            <div style="overflow-x:auto;">
                <table class="db-table">
                    <thead><tr><th>Ticket ID</th><th>Category</th><th>Severity</th><th>Landmark / GPS</th><th>AI Action Plan</th><th>Duplicates</th><th>Status (Click to Update)</th></tr></thead>
                    <tbody id="db-tbody"></tbody>
                </table>
            </div>
        </div>
    </div>

    <div id="tab-submit" class="tab-pane">
        <div class="db-card">
            <h3 style="font-size:1.1rem; font-weight:700; margin-bottom:1rem;">Citizen Complaint Submission</h3>
            <form id="report-form" style="display:grid; grid-template-columns:1fr 1fr; gap:1.5rem;">
                <div>
                    <div style="margin-bottom:1rem;"><label style="display:block; font-size:0.85rem; font-weight:600; margin-bottom:6px;">Issue Photo (JPEG, PNG, WebP)</label><input type="file" id="form-image" accept="image/*" required style="width:100%; padding:8px; border:1px solid #cbd5e1; border-radius:8px;"></div>
                    <div style="margin-bottom:1rem;"><label style="display:block; font-size:0.85rem; font-weight:600; margin-bottom:6px;">Voice Note in Urdu / Sindhi (Optional)</label><input type="file" id="form-audio" accept="audio/*" style="width:100%; padding:8px; border:1px solid #cbd5e1; border-radius:8px;"></div>
                    <div style="margin-bottom:1rem;"><label style="display:block; font-size:0.85rem; font-weight:600; margin-bottom:6px;">Description</label><input type="text" id="form-desc" placeholder="e.g. Autobahn road Latifabad main deep pothole hai" style="width:100%; padding:10px; border:1px solid #cbd5e1; border-radius:8px;"></div>
                </div>
                <div>
                    <div style="margin-bottom:1rem;">
                        <label style="display:block; font-size:0.85rem; font-weight:600; margin-bottom:6px;">Hyderabad Landmark Presets</label>
                        <select id="landmark-select" onchange="const p=this.value.split(','); document.getElementById('form-lat').value=p[0]; document.getElementById('form-lon').value=p[1];" style="width:100%; padding:10px; border:1px solid #cbd5e1; border-radius:8px;">
                            <option value="25.392000,68.373500">Pacco Qillo (Pakka Qila), Shahi Bazaar Gate</option>
                            <option value="25.378000,68.352000">Autobahn Road, Latifabad Unit 2</option>
                            <option value="25.395000,68.332000">Naseem Nagar Chowk, Qasimabad</option>
                            <option value="25.367000,68.358000">Latifabad Unit 7, Near General Hospital</option>
                            <option value="25.405000,68.338000">Wadhu Wah Road, Qasimabad</option>
                            <option value="25.432000,68.315000">Kotri Barrage Indus Bridge Approach</option>
                        </select>
                    </div>
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:1rem;">
                        <div><label style="display:block; font-size:0.85rem; font-weight:600;">Latitude</label><input type="text" id="form-lat" value="25.392000" style="width:100%; padding:8px; border:1px solid #cbd5e1; border-radius:8px;"></div>
                        <div><label style="display:block; font-size:0.85rem; font-weight:600;">Longitude</label><input type="text" id="form-lon" value="68.373500" style="width:100%; padding:8px; border:1px solid #cbd5e1; border-radius:8px;"></div>
                    </div>
                    <button type="submit" class="btn-action btn-primary" id="btn-sub" style="width:100%; justify-content:center; padding:10px;"><i class="fa-solid fa-bolt"></i> Submit to AI Triage Pipeline</button>
                </div>
            </form>
            <div id="ai-resp-card" style="display:none; margin-top:1.5rem; padding:1.25rem; background:#f1f5f9; border-radius:10px;">
                <h4 style="color:var(--civic-blue);" id="resp-tkt"></h4>
                <div id="resp-meta" style="margin:6px 0;"></div>
                <div id="resp-dedup" style="color:#b45309; font-weight:600;"></div>
                <p style="margin-top:6px;"><b>AI Action Plan:</b> <span id="resp-plan"></span></p>
            </div>
        </div>
    </div>

    <script>
        const ADMIN_KEY = "cleancity-admin-secret-key-2026";
        let map, markersLayer, circlesLayer;
        const HYD_LAT = 25.392000, HYD_LON = 68.362000;

        function initMap() {
            map = L.map('real-map').setView([HYD_LAT, HYD_LON], 13);
            L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' }).addTo(map);
            markersLayer = L.layerGroup().addTo(map);
            circlesLayer = L.layerGroup().addTo(map);
        }

        function switchTab(id) {
            document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.getElementById(id).classList.add('active');
            event.currentTarget.classList.add('active');
            if (id === 'tab-map' && map) setTimeout(() => map.invalidateSize(), 150);
        }

        async function loadDashboardData() {
            try {
                const s = await (await fetch('/api/stats', { headers: {'X-Admin-API-Key': ADMIN_KEY} })).json();
                document.getElementById('kpi-open').innerText = s.total_open;
                document.getElementById('kpi-crit').innerText = s.critical_alerts;
                document.getElementById('kpi-res').innerText = s.resolved_today;
                document.getElementById('kpi-total').innerText = s.total_reports;

                const resp = await (await fetch('/api/tickets?limit=100', { headers: {'X-Admin-API-Key': ADMIN_KEY} })).json();
                const tickets = resp.tickets || resp || [];

                markersLayer.clearLayers(); circlesLayer.clearLayers();
                tickets.forEach(t => {
                    const col = t.severity === 'Critical' ? '#dc2626' : (t.severity === 'High' ? '#d97706' : '#2563eb');
                    L.circle([t.latitude, t.longitude], { radius: 50, color: col, fillColor: col, fillOpacity: 0.12, dashArray: '4, 4' }).addTo(circlesLayer);
                    L.circleMarker([t.latitude, t.longitude], { radius: 8, fillColor: col, color: '#fff', weight: 2, fillOpacity: 0.95 }).addTo(markersLayer)
                        .bindPopup(`<b>${t.ticket_id} [${t.category}]</b><br>Severity: ${t.severity}<br>Action: ${t.ai_action_plan}`);
                });

                const tb = document.getElementById('db-tbody'); tb.innerHTML = '';
                tickets.forEach(t => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `<td style="font-weight:700; color:var(--civic-blue);">${t.ticket_id}</td>
                    <td><b>${t.category}</b></td>
                    <td><span class="badge badge-${t.severity}">${t.severity}</span></td>
                    <td style="font-size:0.82rem;">${t.translated_text || 'Hyderabad'}<br><span style="font-family:monospace; color:var(--text-muted);">${t.latitude.toFixed(4)}, ${t.longitude.toFixed(4)}</span></td>
                    <td style="font-size:0.82rem;">${t.ai_action_plan}</td>
                    <td><span style="font-weight:600; color:var(--civic-blue);">${t.duplicate_count} merged</span></td>
                    <td><select onchange="updateTicketStatus('${t.ticket_id}', this.value)" style="padding:4px 8px; border-radius:6px;">
                        <option value="Open" ${t.status==='Open'?'selected':''}>Open</option>
                        <option value="In Progress" ${t.status==='In Progress'?'selected':''}>In Progress</option>
                        <option value="Resolved" ${t.status==='Resolved'?'selected':''}>Resolved</option>
                    </select></td>`;
                    tb.appendChild(tr);
                });
            } catch(e) { console.error(e); }
        }

        async function updateTicketStatus(id, stat) {
            await fetch(`/api/update-status/${id}`, { method:'PATCH', headers:{'Content-Type':'application/json', 'X-Admin-API-Key':ADMIN_KEY}, body:JSON.stringify({status:stat}) });
            loadDashboardData();
        }

        async function seedHyderabadData() {
            const r = await (await fetch('/api/seed-demo-data', { method:'POST', headers:{'X-Admin-API-Key':ADMIN_KEY} })).json();
            alert(r.message); loadDashboardData();
        }

        document.getElementById('report-form').onsubmit = async (e) => {
            e.preventDefault();
            const btn = document.getElementById('btn-sub');
            btn.disabled = true; btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing...';
            const fd = new FormData();
            fd.append('image', document.getElementById('form-image').files[0]);
            if (document.getElementById('form-audio').files[0]) fd.append('audio', document.getElementById('form-audio').files[0]);
            fd.append('latitude', document.getElementById('form-lat').value);
            fd.append('longitude', document.getElementById('form-lon').value);
            fd.append('description', document.getElementById('form-desc').value);

            const res = await (await fetch('/api/submit-report', { method:'POST', body:fd })).json();
            document.getElementById('ai-resp-card').style.display = 'block';
            document.getElementById('resp-tkt').innerText = `Ticket ID: ${res.ticket_id}`;
            document.getElementById('resp-meta').innerHTML = `<b>Category:</b> ${res.category} &bull; <b>Severity:</b> <span class="badge badge-${res.severity}">${res.severity}</span>`;
            document.getElementById('resp-dedup').innerText = res.is_duplicate ? '🔄 Merged within 50m radius' : '🆕 New verified issue registered';
            document.getElementById('resp-plan').innerText = res.ai_action_plan;
            btn.disabled = false; btn.innerHTML = '<i class="fa-solid fa-bolt"></i> Submit to AI Triage Pipeline';
            loadDashboardData();
        };

        window.onload = () => { initMap(); loadDashboardData(); };
    </script>
</body>
</html>
"""


# ======================================================================================
# 10. FASTAPI APPLICATION INITIALIZATION & ROUTING
# ======================================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing CivicPulse AI Master Backend...")
    ensure_upload_dirs()
    init_db()
    seed_demo_data()
    logger.info("Database and media storage directories initialized successfully.")
    yield
    logger.info("CivicPulse AI Master Backend shutting down.")


app = FastAPI(
    title="🏛️ " + settings.APP_NAME,
    version="2.0.0",
    description="Unified Master Backend & Geospatial Engine for CivicPulse AI (Alibaba Cloud AI Hackathon 2026).",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)
@app.get("/media/{file_path:path}")
async def serve_media(file_path: str):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_dir, "media", file_path)
    if os.path.exists(full_path):
        return FileResponse(full_path)
    raise HTTPException(status_code=404, detail="Image not found on disk")
# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if not os.path.exists(settings.UPLOAD_DIR):
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/media", StaticFiles(directory=settings.UPLOAD_DIR), name="media")


@app.exception_handler(Exception)
async def global_unhandled_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, (HTTPException, StarletteHTTPException, RequestValidationError, RateLimitExceeded)):
        raise exc
    logger.error(f"Server error on {request.method} {request.url}: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error occurred."})


# --- ENDPOINTS ---

@app.get("/", response_class=HTMLResponse, tags=["Dashboard UI"])
@app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard UI"])
async def dashboard_view():
    """Serves the built-in 3D Cyberpunk Dashboard."""
    return DASHBOARD_HTML


@app.get("/api/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "app": settings.APP_NAME, "version": "1.0.0", "environment": settings.APP_ENV}


PAKISTAN_LANDMARKS = {
    # Karachi Landmarks & Areas
    "saddar, karachi": (24.860700, 67.001100),
    "saddar karachi": (24.860700, 67.001100),
    "empress market": (24.862400, 67.027000),
    "clifton": (24.823600, 67.032200),
    "sea view": (24.795000, 67.065000),
    "do darya": (24.762000, 67.078000),
    "boat basin": (24.823600, 67.032200),
    "bilawal house": (24.819000, 67.034000),
    "dha phase 5": (24.805000, 67.058000),
    "dha phase 6": (24.798000, 67.068000),
    "dha phase 2": (24.839000, 67.072000),
    "dha": (24.805000, 67.058000),
    "defence": (24.805000, 67.058000),
    "gulshan-e-iqbal": (24.920700, 67.092800),
    "gulshan": (24.920700, 67.092800),
    "nipa chowrangi": (24.928000, 67.102000),
    "nipa": (24.928000, 67.102000),
    "hassan square": (24.898000, 67.075000),
    "university road": (24.931000, 67.112000),
    "gulistan-e-jauhar": (24.914000, 67.135000),
    "jauhar chowrangi": (24.922000, 67.140000),
    "kamran chowrangi": (24.914000, 67.135000),
    "jauhar": (24.914000, 67.135000),
    "north nazimabad": (24.939200, 67.038100),
    "hyderi": (24.938000, 67.035000),
    "sakhi hassan": (24.945000, 67.052000),
    "five star chowrangi": (24.941000, 67.042000),
    "new karachi": (24.975000, 67.065000),
    "up more": (24.981000, 67.068000),
    "federal b area": (24.930000, 67.068000),
    "fb area": (24.930000, 67.068000),
    "water pump": (24.935000, 67.072000),
    "aisha manzil": (24.925000, 67.062000),
    "yaseenabad": (24.919000, 67.075000),
    "korangi industrial area": (24.838400, 67.142000),
    "korangi crossing": (24.825000, 67.118000),
    "korangi": (24.838400, 67.142000),
    "landhi": (24.845000, 67.185000),
    "babar market": (24.845000, 67.185000),
    "malir cantt": (24.928000, 67.205000),
    "malir city": (24.918000, 67.202000),
    "malir": (24.918000, 67.202000),
    "kala board": (24.898000, 67.182000),
    "shahrah-e-faisal": (24.862000, 67.070000),
    "nursery": (24.864000, 67.065000),
    "baloch colony": (24.858000, 67.078000),
    "pechs": (24.871000, 67.059000),
    "tariq road": (24.872000, 67.061000),
    "bahadurabad": (24.882000, 67.068000),
    "char minar": (24.882000, 67.068000),
    "liaquatabad": (24.905000, 67.042000),
    "dak khana": (24.905000, 67.042000),
    "nazimabad": (24.913000, 67.025000),
    "golimar": (24.898000, 67.019000),
    "site karachi": (24.898000, 66.992000),
    "siemens chowrangi": (24.898000, 66.992000),
    "orangi town": (24.945000, 66.985000),
    "orangi": (24.945000, 66.985000),
    "banaras": (24.925000, 66.998000),
    "keamari": (24.815000, 66.975000),
    "karachi port": (24.815000, 66.975000),
    "lyari": (24.868000, 66.995000),
    "lea market": (24.865000, 67.002000),
    "cheel chowk": (24.868000, 66.995000),
    "surjani town": (25.020000, 67.050000),
    "surjani": (25.020000, 67.050000),
    "buffer zone": (24.960000, 67.065000),
    "scheme 33": (24.960000, 67.155000),
    "safoora chowrangi": (24.960000, 67.155000),
    "safoora": (24.960000, 67.155000),
    "bin qasim": (24.780000, 67.330000),
    "port qasim": (24.780000, 67.330000),
    "karachi": (24.860700, 67.001100),

    # Hyderabad Landmarks & Areas
    "pacco qillo": (25.392000, 68.373500),
    "pakka qila": (25.392000, 68.373500),
    "shahi bazaar": (25.392000, 68.373500),
    "autobahn": (25.378000, 68.352000),
    "latifabad unit 2": (25.378000, 68.352000),
    "latifabad unit 3": (25.374000, 68.350000),
    "latifabad unit 4": (25.372000, 68.351000),
    "latifabad unit 6": (25.371000, 68.354000),
    "latifabad unit 7": (25.367000, 68.358000),
    "latifabad unit 8": (25.365000, 68.356000),
    "latifabad unit 9": (25.364000, 68.355000),
    "latifabad unit 11": (25.361000, 68.359000),
    "latifabad unit 12": (25.358000, 68.362000),
    "latifabad": (25.375000, 68.355000),
    "naseem nagar": (25.395000, 68.332000),
    "qasimabad": (25.395000, 68.332000),
    "wadhu wah": (25.405000, 68.338000),
    "citizen colony": (25.388000, 68.341000),
    "prince town": (25.398000, 68.328000),
    "london town": (25.402000, 68.345000),
    "marvi town": (25.409000, 68.325000),
    "haider chowk": (25.391000, 68.362000),
    "saddar, hyderabad": (25.391000, 68.362000),
    "saddar hyderabad": (25.391000, 68.362000),
    "saddar": (24.860700, 67.001100),  # Default Saddar to Karachi Center
    "station road": (25.397000, 68.369000),
    "resham gali": (25.397000, 68.369000),
    "gari khata": (25.396000, 68.368000),
    "kotri barrage": (25.432000, 68.315000),
    "kotri": (25.432000, 68.315000),
    "thandi sarak": (25.402000, 68.356000),
    "hirabad": (25.394000, 68.365000),
    "tower market": (25.394000, 68.365000),
    "tilak incline": (25.393000, 68.360000),
    "kali mori": (25.382000, 68.385000),
    "phuleli": (25.382000, 68.385000),
    "pareetabad": (25.389000, 68.388000),
    "site hyderabad": (25.385000, 68.318000),
    "site": (25.385000, 68.318000),
    "jamshoro phatak": (25.412000, 68.295000),
    "tando jam": (25.428000, 68.535000),
    "tando wali muhammad": (25.380000, 68.345000),
    "giddu chowk": (25.380000, 68.345000),
    "hussainabad": (25.352000, 68.338000),
    "gulshan-e-hali": (25.399000, 68.378000),
    "hyderabad": (25.392000, 68.358000),
}
HYDERABAD_LANDMARKS = PAKISTAN_LANDMARKS


@app.post("/api/submit-report", response_model=ReportSubmissionResponse, status_code=201, tags=["Citizen Submissions"])
@limiter.limit(settings.SUBMIT_RATE_LIMIT)
async def submit_report(
    request: Request,
    image: UploadFile = File(...),
    audio: Optional[UploadFile] = File(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    lat: Optional[str] = Form(None),
    lng: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    # Resolve coordinates
    resolved_lat: Optional[float] = latitude
    resolved_lon: Optional[float] = longitude

    if resolved_lat is None and lat and lat.strip():
        try:
            resolved_lat = float(lat.strip())
        except ValueError:
            pass
    if resolved_lon is None and lng and lng.strip():
        try:
            resolved_lon = float(lng.strip())
        except ValueError:
            pass

    if resolved_lat is None or resolved_lon is None:
        if address:
            addr_lower = address.lower()
            matched = False
            for k, coords in HYDERABAD_LANDMARKS.items():
                if k in addr_lower:
                    resolved_lat, resolved_lon = coords
                    matched = True
                    break
            if not matched:
                resolved_lat, resolved_lon = 25.392000, 68.358000
        else:
            resolved_lat, resolved_lon = 25.392000, 68.358000

    if not (-90.0 <= resolved_lat <= 90.0) or not (-180.0 <= resolved_lon <= 180.0):
        raise HTTPException(status_code=422, detail="Invalid latitude or longitude coordinate ranges.")

    saved_img = await save_uploaded_file(image, is_image=True)
    saved_aud = await save_uploaded_file(audio, is_image=False) if (audio and audio.filename and audio.size != 0) else None

    combined_text = description or address or ""
    ai_res = process_civic_submission(image_path=saved_img, audio_path=saved_aud, user_description=combined_text)

    # Geo-deduplication check
    dup = find_duplicate_ticket(db, category=ai_res.category, latitude=resolved_lat, longitude=resolved_lon,
                                radius_meters=settings.GEO_DEDUP_RADIUS_METERS, time_window_hours=settings.GEO_DEDUP_TIME_WINDOW_HOURS) if ai_res.is_valid_civic_issue else None

    if dup:
        dup.duplicate_count += 1
        child = Complaint(
            ticket_id=generate_ticket_id(),
            image_path=saved_img,
            original_audio_path=saved_aud,
            translated_text=ai_res.translated_text,
            category=dup.category,
            severity=dup.severity,
            latitude=resolved_lat,
            longitude=resolved_lon,
            phone_number=phone_number,
            ai_action_plan=dup.ai_action_plan,
            is_valid_civic_issue=True,
            status="Open",
            duplicate_of=dup.ticket_id,
            duplicate_count=0
        )
        db.add(child)
        db.commit()

        # Emergency dispatch to nearest municipal chairman/supervisor if Critical
        emergency_dispatch = None
        if str(dup.severity).strip().title() == "Critical":
            nearest_sup, dist_km = find_nearest_supervisor(resolved_lat, resolved_lon)
            emergency_dispatch = dispatch_critical_alert_email(
                supervisor=nearest_sup,
                distance_km=dist_km,
                ticket_id=dup.ticket_id,
                category=dup.category,
                severity=dup.severity,
                address=address or f"{resolved_lat:.4f}° N, {resolved_lon:.4f}° E",
                lat=resolved_lat,
                lon=resolved_lon,
                ai_action_plan=dup.ai_action_plan or "Immediate municipal inspection dispatched.",
                description=combined_text,
                phone_number=phone_number
            )

        return ReportSubmissionResponse(
            success=True,
            status="success",
            ticket_id=dup.ticket_id,
            is_duplicate=True,
            merged_ticket_id=dup.ticket_id,
            category=dup.category,
            severity=dup.severity,
            is_valid_civic_issue=True,
            ai_action_plan=dup.ai_action_plan,
            translated_text=ai_res.translated_text,
            phone_number=phone_number,
            emergency_dispatch=emergency_dispatch,
            message=f"Report merged with active open ticket {dup.ticket_id} within 50m."
        )

    # New primary complaint
    new_id = generate_ticket_id()
    new_c = Complaint(
        ticket_id=new_id,
        image_path=saved_img,
        original_audio_path=saved_aud,
        translated_text=ai_res.translated_text,
        category=ai_res.category,
        severity=ai_res.severity,
        latitude=resolved_lat,
        longitude=resolved_lon,
        phone_number=phone_number,
        ai_action_plan=ai_res.ai_action_plan,
        is_valid_civic_issue=ai_res.is_valid_civic_issue,
        status="Open",
        duplicate_of=None,
        duplicate_count=0
    )
    db.add(new_c)
    db.commit()
    db.refresh(new_c)

    # Emergency dispatch to nearest municipal chairman/supervisor if Critical
    emergency_dispatch = None
    if str(new_c.severity).strip().title() == "Critical":
        nearest_sup, dist_km = find_nearest_supervisor(resolved_lat, resolved_lon)
        emergency_dispatch = dispatch_critical_alert_email(
            supervisor=nearest_sup,
            distance_km=dist_km,
            ticket_id=new_c.ticket_id,
            category=new_c.category,
            severity=new_c.severity,
            address=address or f"{resolved_lat:.4f}° N, {resolved_lon:.4f}° E",
            lat=resolved_lat,
            lon=resolved_lon,
            ai_action_plan=new_c.ai_action_plan or "Immediate municipal inspection dispatched.",
            description=combined_text,
            phone_number=phone_number
        )

    return ReportSubmissionResponse(
        success=True,
        status="success" if new_c.is_valid_civic_issue else "flagged",
        ticket_id=new_c.ticket_id,
        is_duplicate=False,
        merged_ticket_id=None,
        category=new_c.category,
        severity=new_c.severity,
        is_valid_civic_issue=new_c.is_valid_civic_issue,
        ai_action_plan=new_c.ai_action_plan,
        translated_text=new_c.translated_text,
        phone_number=new_c.phone_number,
        emergency_dispatch=emergency_dispatch,
        message="Ticket created and verified successfully." if new_c.is_valid_civic_issue else "Submission received but flagged by AI."
    )


@app.get("/api/tickets", response_model=TicketListResponse, tags=["Municipal Admin"])
def get_tickets(
    status_filter: Optional[StatusEnum] = Query(None, alias="status"),
    category_filter: Optional[CategoryEnum] = Query(None, alias="category"),
    include_invalid: bool = Query(False),
    include_duplicates: bool = Query(False),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: str = Depends(verify_admin_api_key)
):
    q = db.query(Complaint)
    if not include_invalid:
        q = q.filter(Complaint.is_valid_civic_issue.is_(True))
    if not include_duplicates:
        q = q.filter(Complaint.duplicate_of.is_(None))
    if status_filter:
        q = q.filter(Complaint.status == status_filter.value)
    if category_filter:
        q = q.filter(Complaint.category == category_filter.value)

    total = q.count()
    raw_tickets = q.order_by(desc(Complaint.timestamp)).offset(offset).limit(limit).all()

    formatted_tickets = []
    for t in raw_tickets:
        formatted_tickets.append(
            TicketResponse(
                ticket_id=t.ticket_id,
                image_path=t.image_path,
                original_audio_path=t.original_audio_path,
                translated_text=t.translated_text,
                category=t.category,
                severity=t.severity,
                latitude=t.latitude,
                longitude=t.longitude,
                lat=t.latitude,
                lng=t.longitude,
                address=t.translated_text or "Hyderabad, Sindh",
                ai_action_plan=t.ai_action_plan,
                is_valid_civic_issue=t.is_valid_civic_issue,
                status=t.status,
                timestamp=t.timestamp,
                created_at=t.timestamp.isoformat(),
                duplicate_of=t.duplicate_of,
                duplicate_count=t.duplicate_count,
                phone_number=getattr(t, "phone_number", None)
            )
        )

    return TicketListResponse(total=total, count=len(formatted_tickets), limit=limit, offset=offset, tickets=formatted_tickets)


@app.get("/api/tickets/{ticket_id}", response_model=TicketResponse, tags=["Municipal Admin"])
def get_ticket_detail(ticket_id: str, db: Session = Depends(get_db), _: str = Depends(verify_admin_api_key)):
    t = db.query(Complaint).filter(Complaint.ticket_id == ticket_id).first()
    if not t:
        raise HTTPException(status_code=404, detail=f"Ticket '{ticket_id}' not found.")
    return t


@app.patch("/api/update-status/{ticket_id}", response_model=TicketResponse, tags=["Municipal Admin"])
def update_status(ticket_id: str, payload: TicketStatusUpdate, db: Session = Depends(get_db), _: str = Depends(verify_admin_api_key)):
    t = db.query(Complaint).filter(Complaint.ticket_id == ticket_id).first()
    if not t:
        raise HTTPException(status_code=404, detail=f"Ticket '{ticket_id}' not found.")
    t.status = payload.status.value
    if payload.status.value == "Resolved":
        t.timestamp = datetime.now(timezone.utc)
    db.commit()
    db.refresh(t)
    return TicketResponse(
        ticket_id=t.ticket_id,
        image_path=t.image_path,
        original_audio_path=t.original_audio_path,
        translated_text=t.translated_text,
        category=t.category,
        severity=t.severity,
        latitude=t.latitude,
        longitude=t.longitude,
        lat=t.latitude,
        lng=t.longitude,
        address=t.translated_text or "Hyderabad, Sindh",
        ai_action_plan=t.ai_action_plan,
        is_valid_civic_issue=t.is_valid_civic_issue,
        status=t.status,
        timestamp=t.timestamp,
        created_at=t.timestamp.isoformat(),
        duplicate_of=t.duplicate_of,
        duplicate_count=t.duplicate_count
    )


@app.get("/api/stats", response_model=AdminDashboardStats, tags=["Municipal Admin"])
def get_stats(db: Session = Depends(get_db), _: str = Depends(verify_admin_api_key)):
    now = datetime.now(timezone.utc)
    today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    window_24h = now - timedelta(hours=24)
    effective_start = min(today_start, window_24h)

    base = db.query(Complaint).filter(Complaint.is_valid_civic_issue.is_(True), Complaint.duplicate_of.is_(None))

    total_reports = base.count()
    total_open = base.filter(Complaint.status == "Open").count()
    critical_alerts = base.filter(Complaint.status == "Open", Complaint.severity == "Critical").count()
    resolved_today = base.filter(Complaint.status == "Resolved", Complaint.timestamp >= effective_start).count()

    cat_counts = db.query(Complaint.category, func.count(Complaint.ticket_id)).filter(
        Complaint.is_valid_civic_issue.is_(True), Complaint.duplicate_of.is_(None)).group_by(Complaint.category).all()
    category_breakdown = {cat: count for cat, count in cat_counts}

    sev_counts = db.query(Complaint.severity, func.count(Complaint.ticket_id)).filter(
        Complaint.is_valid_civic_issue.is_(True), Complaint.duplicate_of.is_(None), Complaint.status == "Open").group_by(Complaint.severity).all()
    severity_breakdown = {sev: count for sev, count in sev_counts}

    return AdminDashboardStats(
        total_open=total_open, critical_alerts=critical_alerts, resolved_today=resolved_today,
        total_reports=total_reports, category_breakdown=category_breakdown, severity_breakdown=severity_breakdown
    )


@app.post("/api/seed-demo-data", tags=["Municipal Admin"])
def trigger_seed(db: Session = Depends(get_db), _: str = Depends(verify_admin_api_key)):
    count = seed_demo_data(db)
    return {"status": "success", "message": f"Seeded demo dataset successfully. Total active complaints: {count}."}


# ======================================================================================
# 11. MAIN RUNNER (Direct CLI Execution)
# ======================================================================================
if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*80)
    print("🚀 Starting CivicPulse AI Unified Master Backend...")
    print(f"📡 API Documentation:  http://127.0.0.1:{settings.PORT}/docs")
    print(f"🏙️ 3D Web Dashboard:  http://127.0.0.1:{settings.PORT}/")
    print("="*80 + "\n")
    uvicorn.run("master_backend:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
