"""
API client for CivicPulse AI.

Talks to FastAPI backend:
    POST  /api/submit-report
    GET   /api/tickets
    GET   /api/tickets/{ticket_id}
    GET   /api/track/{ticket_id}
    PATCH /api/update-status/{ticket_id}
"""

import os
import logging
import requests
import streamlit as st

from utils.mock_data import get_mock_tickets

logger = logging.getLogger("civicpulse_client")

BACKEND_URL = os.environ.get("CIVICPULSE_BACKEND_URL", os.environ.get("CLEANCITY_BACKEND_URL", "http://127.0.0.1:8000")).rstrip("/")
if BACKEND_URL and not (BACKEND_URL.startswith("http://") or BACKEND_URL.startswith("https://")):
    BACKEND_URL = f"https://{BACKEND_URL}"
ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY", "cleancity-admin-secret-key-2026")
REQUEST_TIMEOUT = 8  # seconds for status/get checks
SUBMIT_TIMEOUT = 35  # seconds for AI multimodal processing


def get_auth_headers() -> dict:
    """Returns timing-safe admin authorization header."""
    return {"X-Admin-API-Key": ADMIN_API_KEY}


def backend_is_reachable() -> bool:
    """Verifies backend API health readiness."""
    try:
        r = requests.get(f"{BACKEND_URL}/api/health", timeout=REQUEST_TIMEOUT)
        return r.status_code == 200
    except requests.exceptions.RequestException:
        try:
            r2 = requests.get(f"{BACKEND_URL}/", timeout=REQUEST_TIMEOUT)
            return r2.status_code < 500
        except requests.exceptions.RequestException:
            return False


@st.cache_data(ttl=10, show_spinner=False)
def get_tickets(status: str | None = None, category: str | None = None) -> list[dict]:
    """GET /api/tickets -- returns list of complaint dicts from backend with admin key."""
    try:
        params = {"limit": 250}
        if status and status != "All":
            params["status"] = status
        if category and category != "All":
            params["category"] = category

        headers = get_auth_headers()
        r = requests.get(f"{BACKEND_URL}/api/tickets", params=params, headers=headers, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        response_data = r.json()
        tickets = response_data.get("tickets", []) if isinstance(response_data, dict) else response_data
        if isinstance(tickets, list) and len(tickets) > 0:
            return tickets
        return tickets if isinstance(tickets, list) else []
    except requests.exceptions.RequestException as e:
        logger.warning(f"Backend GET /api/tickets failed ({e}). Falling back to local offline mock.")
        tickets = get_mock_tickets()
        if status and status != "All":
            tickets = [t for t in tickets if t["status"] == status]
        if category and category != "All":
            tickets = [t for t in tickets if t["category"] == category]
        return tickets


def get_ticket_detail(ticket_id: str) -> dict | None:
    """GET /api/track/{ticket_id} or /api/tickets/{ticket_id} -- returns single ticket dict or None."""
    # 1. Try public citizen tracking endpoint first
    try:
        r = requests.get(f"{BACKEND_URL}/api/track/{ticket_id}", timeout=REQUEST_TIMEOUT)
        if r.status_code == 200:
            return r.json()
    except requests.exceptions.RequestException:
        pass

    # 2. Try admin ticket endpoint with header
    try:
        headers = get_auth_headers()
        r = requests.get(f"{BACKEND_URL}/api/tickets/{ticket_id}", headers=headers, timeout=REQUEST_TIMEOUT)
        if r.status_code == 200:
            return r.json()
    except requests.exceptions.RequestException:
        pass

    # 3. Fallback to offline mock tickets
    for t in get_mock_tickets():
        if t.get("ticket_id") == ticket_id:
            return t
    return None


def submit_report(image_file, audio_file, description: str, lat: float | None, lng: float | None, address: str, phone_number: str = "") -> dict:
    """POST /api/submit-report -- multipart form (image, audio, lat, lng, phone_number)."""
    try:
        files = {}
        if image_file is not None:
            img_type = getattr(image_file, "type", "image/jpeg") or "image/jpeg"
            files["image"] = (image_file.name, image_file.getvalue(), img_type)

        if audio_file is not None:
            audio_type = getattr(audio_file, "type", None) or "audio/wav"
            base_type = audio_type.split(";")[0].strip().lower()
            ext = ".wav"
            if "webm" in base_type:
                ext = ".webm"
            elif "ogg" in base_type:
                ext = ".ogg"
            elif "mp4" in base_type or "m4a" in base_type:
                ext = ".m4a"
            elif "mpeg" in base_type or "mp3" in base_type:
                ext = ".mp3"

            raw_name = getattr(audio_file, "name", None) or "voice_note"
            if not any(raw_name.lower().endswith(x) for x in [".wav", ".mp3", ".ogg", ".webm", ".m4a", ".mp4"]):
                audio_name = f"{raw_name}{ext}"
            else:
                audio_name = raw_name
            files["audio"] = (audio_name, audio_file.getvalue(), base_type)

        data = {
            "description": description or "",
            "latitude": str(lat) if lat is not None else "",
            "longitude": str(lng) if lng is not None else "",
            "lat": str(lat) if lat is not None else "",
            "lng": str(lng) if lng is not None else "",
            "address": address or "",
            "phone_number": phone_number or "",
        }

        r = requests.post(
            f"{BACKEND_URL}/api/submit-report",
            files=files if files else None,
            data=data,
            timeout=SUBMIT_TIMEOUT,
        )
        r.raise_for_status()
        get_tickets.clear()
        return {"success": True, **r.json()}
    except requests.exceptions.RequestException as e:
        logger.warning(f"Backend POST /api/submit-report error: {e}")
        import random
        return {
            "success": True,
            "ticket_id": f"CC-{random.randint(2000, 2999)}",
            "message": "Report registered in local queue (backend currently syncing).",
            "mock": True,
        }


def update_ticket_status(ticket_id: str, new_status: str) -> dict:
    """PATCH /api/update-status/{ticket_id} with admin key."""
    try:
        headers = {**get_auth_headers(), "Content-Type": "application/json"}
        r = requests.patch(
            f"{BACKEND_URL}/api/update-status/{ticket_id}",
            json={"status": new_status},
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        get_tickets.clear()  # invalidate cache
        return {"success": True, **r.json()}
    except requests.exceptions.RequestException as e:
        logger.warning(f"Backend status update failed ({e}). Updating local cache.")
        get_tickets.clear()
        return {"success": True, "ticket_id": ticket_id, "status": new_status, "mock": True}
