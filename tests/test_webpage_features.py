import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_privacy_policy_page():
    """Verify /privacy returns 200 and has privacy policy content."""
    res = client.get("/privacy")
    assert res.status_code == 200
    assert "Privacy Policy" in res.text
    assert "PECA 2016" in res.text
    assert "Geolocation" in res.text

def test_terms_and_conditions_page():
    """Verify /terms returns 200 and has terms content."""
    res = client.get("/terms")
    assert res.status_code == 200
    assert "Terms" in res.text
    assert "Acceptance" in res.text
    assert "Sindh" in res.text

def test_robots_txt():
    """Verify /robots.txt returns valid robots directives."""
    res = client.get("/robots.txt")
    assert res.status_code == 200
    assert "User-agent:" in res.text
    assert "Disallow: /media/" in res.text
    assert "sitemap.xml" in res.text

def test_sitemap_xml():
    """Verify /sitemap.xml returns valid XML."""
    res = client.get("/sitemap.xml")
    assert res.status_code == 200
    assert "urlset" in res.text
    assert "<loc>" in res.text

def test_favicon():
    """Verify /favicon.ico is accessible."""
    res = client.get("/favicon.ico")
    assert res.status_code == 200

def test_security_headers():
    """Verify HTTPS and security headers are attached to responses."""
    res = client.get("/api/health")
    assert res.status_code == 200
    assert "Strict-Transport-Security" in res.headers
    assert res.headers["X-Content-Type-Options"] == "nosniff"
    assert res.headers["X-Frame-Options"] == "SAMEORIGIN"

def test_honeypot_bot_protection():
    """Verify submissions filled with honeypot field are rejected as bot spam."""
    files = {"image": ("dummy.jpg", b"fake-jpg-content", "image/jpeg")}
    data = {
        "address": "Haider Chowk, Hyderabad",
        "hp_website": "http://spambot.evil.com",  # Honeypot filled!
        "latitude": "25.392000",
        "longitude": "68.362000"
    }
    res = client.post("/api/submit-report", files=files, data=data)
    assert res.status_code == 400
    assert "bot" in res.text.lower()

def test_custom_404_html():
    """Verify custom 404 page is served for non-existent HTML requests."""
    res = client.get("/non-existent-page", headers={"Accept": "text/html"})
    assert res.status_code == 404
    assert "404" in res.text
    assert "Municipal Record Not Found" in res.text

def test_analytics_event_endpoint():
    """Verify anonymous analytics events can be recorded."""
    payload = {"event": "test_page_view", "payload": {"path": "/"}, "timestamp": 1234567890}
    res = client.post("/api/analytics/event", json=payload)
    assert res.status_code == 200
    assert res.json()["status"] == "recorded"
