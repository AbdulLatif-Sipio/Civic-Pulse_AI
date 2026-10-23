"""
API client for CivicPulse AI.

Talks to FastAPI backend:
    POST  /api/submit-report
    GET   /api/tickets
    PATCH /api/update-status/{ticket_id}
"""

import os
import requests
import streamlit as st

from utils.mock_data import get_mock_tickets

BACKEND_URL = os.environ.get("CIVICPULSE_BACKEND_URL", os.environ.get("CLEANCITY_BACKEND_URL", "http://localhost:8000"))
REQUEST_TIMEOUT = 5  # seconds for status/get checks
SUBMIT_TIMEOUT = 30  # seconds for AI multimodal processing


def backend_is_reachable() -> bool:
    try:
        r = requests.get(f"{BACKEND_URL}/", timeout=REQUEST_TIMEOUT)
        return r.status_code < 500
    except requests.exceptions.RequestException:
        return False


@st.cache_data(ttl=15, show_spinner=False)
def get_tickets(status: str | None = None, category: str | None = None) -> list[dict]:
    """GET /api/tickets -- returns list of complaint dicts."""
    try:
        params = {}
        if status and status != "All":
            params["status"] = status
        if category and category != "All":
            params["category"] = category
        r = requests.get(f"{BACKEND_URL}/api/tickets", params=params, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        response_data = r.json()
        # Agar data dictionary mein hai toh sirf tickets nikal lo, warna waise hi de do
        return response_data.get("tickets", []) if isinstance(response_data, dict) else response_data
    except requests.exceptions.RequestException:
        # Backend not up yet -- use mock data, apply same filters client-side
        tickets = get_mock_tickets()
        if status and status != "All":
            tickets = [t for t in tickets if t["status"] == status]
        if category and category != "All":
            tickets = [t for t in tickets if t["category"] == category]
        return tickets


def get_ticket_detail(ticket_id: str) -> dict | None:
    """GET /api/tickets/{ticket_id} -- returns single ticket dict or None."""
    try:
        r = requests.get(f"{BACKEND_URL}/api/tickets/{ticket_id}", timeout=REQUEST_TIMEOUT)
        if r.status_code == 200:
            return r.json()
        return None
    except requests.exceptions.RequestException:
        for t in get_mock_tickets():
            if t.get("ticket_id") == ticket_id:
                return t
        return None


def submit_report(image_file, audio_file, description: str, lat: float | None, lng: float | None, address: str, phone_number: str = "") -> dict:
    """POST /api/submit-report -- multipart form (image, audio, lat, lng, phone_number)."""
    try:
        files = {}
        if image_file is not None:
            files["image"] = (image_file.name, image_file.getvalue(), image_file.type)
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
            "lat": lat if lat is not None else "",
            "lng": lng if lng is not None else "",
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
        return {"success": True, **r.json()}
    except requests.exceptions.RequestException:
        # Mock success response, mirrors expected backend shape
        import random
        return {
            "success": True,
            "ticket_id": f"CC-{random.randint(2000, 2999)}",
            "message": "Report submitted (demo mode -- backend not connected yet).",
            "mock": True,
        }


def update_ticket_status(ticket_id: str, new_status: str) -> dict:
    """PATCH /api/update-status/{ticket_id}"""
    try:
        r = requests.patch(
            f"{BACKEND_URL}/api/update-status/{ticket_id}",
            json={"status": new_status},
            timeout=REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        get_tickets.clear()  # invalidate cache
        return {"success": True, **r.json()}
    except requests.exceptions.RequestException:
        get_tickets.clear()
        return {"success": True, "ticket_id": ticket_id, "status": new_status, "mock": True}
