import os
import time
import requests
import datetime
from fastapi import FastAPI, HTTPException, Query
from dotenv import load_dotenv
from typing import Optional, List

load_dotenv()

app = FastAPI(title="KZU Ultimate Timetable API")

USER = os.getenv("INTRANET_USER")
PW = os.getenv("INTRANET_PW")
BASE_URL = "https://intranet.tam.ch/kzu"

# Hilfsfunktion für den Abruf
def fetch_raw_data(days=7):
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0', 'X-Requested-With': 'XMLHttpRequest'})

    # Login
    session.post(BASE_URL, data={'loginschool': 'kzu', 'loginuser': USER, 'loginpassword': PW})

    if 'sturmsession' not in session.cookies:
        raise HTTPException(status_code=401, detail="Login fehlgeschlagen")

    start_ts = int(time.time() * 1000)
    end_ts = start_ts + (days * 24 * 60 * 60 * 1000)

    ajax_url = f"{BASE_URL}/timetable/ajax-get-timetable"
    response = session.post(ajax_url, data={'startDate': start_ts, 'endDate': end_ts, 'holidaysOnly': 0})

    return response.json().get("data", [])

# --- ENDPUNKTE ---

@app.get("/all")
def get_all():
    """Gibt absolut alles zurück (nächste 7 Tage)."""
    return fetch_raw_data()

@app.get("/today")
def get_today():
    """Nur die Lektionen von heute."""
    all_data = fetch_raw_data(days=1)
    today_str = datetime.date.today().isoformat()
    return [d for d in all_data if d.get("lessonDate") == today_str]

@app.get("/week")
def get_week():
    """Daten für die aktuelle Woche."""
    return fetch_raw_data(days=7)

@app.get("/filter/subject/{subject}")
def filter_by_subject(subject: str):
    """Filtert nach einem Fachnamen (z.B. /filter/subject/Mathematik)."""
    all_data = fetch_raw_data(days=14)
    return [d for d in all_data if subject.lower() in str(d.get("lessonName", "")).lower()]

@app.get("/filter/teacher/{acronym}")
def filter_by_teacher(acronym: str):
    """Filtert nach dem Lehrer-Kürzel (z.B. /filter/teacher/nig)."""
    all_data = fetch_raw_data(days=14)
    return [d for d in all_data if acronym.lower() == str(d.get("teacherAcronym", "")).lower()]

@app.get("/filter/room/{room}")
def filter_by_room(room: str):
    """Filtert nach einem Raum (z.B. /filter/room/A06)."""
    all_data = fetch_raw_data(days=7)
    return [d for d in all_data if room.lower() in str(d.get("roomName", "")).lower()]

@app.get("/cancelled")
def get_cancelled():
    """Zeigt nur ausgefallene Lektionen an."""
    all_data = fetch_raw_data(days=14)
    return [d for d in all_data if d.get("timetableEntryTypeShort") == "cancel"]

@app.get("/exams")
def get_exams():
    """Zeigt nur Prüfungen an."""
    all_data = fetch_raw_data(days=30)
    return [d for d in all_data if d.get("isExamLesson") == True]

@app.get("/date/{date_str}")
def get_by_date(date_str: str):
    """Filtert nach einem bestimmten Datum (Format: YYYY-MM-DD, z.B. /date/2026-02-25)."""
    all_data = fetch_raw_data(days=30)
    return [d for d in all_data if d.get("lessonDate") == date_str]

@app.get("/")
def home():
    return {
        "status": "online",
        "endpoints": [
            "/all", "/today", "/week", "/cancelled", "/exams",
            "/filter/subject/{name}", "/filter/teacher/{acronym}",
            "/filter/room/{room}", "/date/{YYYY-MM-DD}"
        ]
    }