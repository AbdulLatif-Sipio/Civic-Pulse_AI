import os
import math
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional, List
from app.config import settings

logger = logging.getLogger(__name__)

EARTH_RADIUS_METERS = 6371000.0


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0) ** 2)
    a = min(1.0, max(0.0, a))
    return EARTH_RADIUS_METERS * (2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a)))


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
    nearest = MUNICIPAL_COMMITTEE_SUPERVISORS[0]
    min_dist_meters = float("inf")
    for sup in MUNICIPAL_COMMITTEE_SUPERVISORS:
        d = haversine_distance_meters(lat, lon, sup["latitude"], sup["longitude"])
        if d < min_dist_meters:
            min_dist_meters = d
            nearest = sup
    distance_km = round(min_dist_meters / 1000.0, 2)
    return nearest, distance_km


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
    subject = f"🚨 [CRITICAL CIVIC ALERT] Immediate Action Required — Ticket #{ticket_id} ({category} at {address})"
    delivery_status = "DELIVERED_SIMULATED_LEDGER"
    
    # Write to audit ledger
    os.makedirs("media", exist_ok=True)
    log_line = f"[{datetime.now(timezone.utc).isoformat()}] DISPATCH -> {supervisor['email']} ({supervisor['name']}) | TICKET: {ticket_id} | HAZARD: {category} (Critical) | DIST: {distance_km}km | ADDR: {address}\n"
    with open("media/critical_alerts.log", "a", encoding="utf-8") as f:
        f.write(log_line)

    return {
        "dispatched": True,
        "delivery_status": delivery_status,
        "recipient_name": supervisor["name"],
        "recipient_designation": supervisor["designation"],
        "recipient_email": supervisor["email"],
        "recipient_phone": supervisor["phone"],
        "zone": supervisor["zone"],
        "city": supervisor["city"],
        "distance_km": distance_km,
        "subject": subject,
        "alert_timestamp": datetime.now(timezone.utc).isoformat()
    }
