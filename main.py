import os
import time
import requests
import datetime
from fastapi import FastAPI, HTTPException, Query
from dotenv import load_dotenv
from typing import List

load_dotenv()

app = FastAPI(title="KZU Ultimate API", description="API für Stundenplan, Filter und Freiräume")

USER = os.getenv("INTRANET_USER")
PW = os.getenv("INTRANET_PW")
BASE_URL = "https://intranet.tam.ch/kzu"

# Zentrale Funktion zum Datenholen
def fetch_kzu_data(start_date: datetime.date, end_date: datetime.date):
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0', 'X-Requested-With': 'XMLHttpRequest'})

    # Login
    session.post(BASE_URL, data={'loginschool': 'kzu', 'loginuser': USER, 'loginpassword': PW})

    if 'sturmsession' not in session.cookies:
        raise HTTPException(status_code=401, detail="Login fehlgeschlagen")

    # Umwandlung in Millisekunden-Timestamps für das Intranet
    start_ts = int(time.mktime(start_date.timetuple()) * 1000)
    end_ts = int(time.mktime(end_date.timetuple()) * 1000)

    ajax_url = f"{BASE_URL}/timetable/ajax-get-timetable"
    payload = {'startDate': start_ts, 'endDate': end_ts, 'holidaysOnly': 0}

    response = session.post(ajax_url, data=payload)
    return response.json().get("data", [])

# --- NEUE ENDPUNKTE ---

@app.get("/range")
def get_range(start: str = Query(..., description="Format: YYYY-MM-DD"),
              end: str = Query(..., description="Format: YYYY-MM-DD")):
    """Holt Daten für einen beliebigen Bereich, z.B. /range?start=2026-03-01&end=2026-03-15"""
    try:
        d1 = datetime.date.fromisoformat(start)
        d2 = datetime.date.fromisoformat(end)
        return fetch_kzu_data(d1, d2)
    except ValueError:
        raise HTTPException(status_code=400, detail="Falsches Datumsformat. Nutze YYYY-MM-DD")

@app.get("/today")
def get_today():
    today = datetime.date.today()
    all_data = fetch_kzu_data(today, today)
    return [d for d in all_data if d.get("lessonDate") == today.isoformat()]

@app.get("/free-rooms")
def get_free_rooms():
    """Zeigt Räume an, die JETZT gerade nicht belegt sind (basierend auf dem heutigen Plan)."""
    today = datetime.date.today()
    now = datetime.datetime.now().time()
    all_lessons = fetch_kzu_data(today, today)

    # Alle Räume, die wir kennen (kannst du erweitern)
    all_rooms = {"A06", "Z101", "Z102", "Z201", "Z205", "Physik1", "Turnhalle"}
    occupied_rooms = set()

    for lesson in all_lessons:
        if lesson.get("lessonDate") == today.isoformat():
            try:
                # Zeiten vergleichen (Format "08:00:00")
                start = datetime.datetime.strptime(lesson["lessonStart"], "%H:%M:%S").time()
                end = datetime.datetime.strptime(lesson["lessonEnd"], "%H:%M:%S").time()

                if start <= now <= end and lesson.get("timetableEntryTypeShort") != "cancel":
                    if lesson.get("roomName"):
                        occupied_rooms.add(lesson["roomName"])
            except:
                continue

    free_rooms = all_rooms - occupied_rooms
    return {
        "time": now.strftime("%H:%M"),
        "occupied": list(occupied_rooms),
        "free": list(free_rooms)
    }

@app.get("/cancelled")
def get_cancelled():
    today = datetime.date.today()
    future = today + datetime.timedelta(days=14)
    data = fetch_kzu_data(today, future)
    return [d for d in data if d.get("timetableEntryTypeShort") == "cancel"]

@app.get("/exams")
def get_exams():
    today = datetime.date.today()
    future = today + datetime.timedelta(days=30)
    data = fetch_kzu_data(today, future)
    return [d for d in data if d.get("isExamLesson") == True]

@app.get("/")
def welcome():
    return {
        "msg": "KZU API Online",
        "endpoints": ["/today", "/range?start=...&end=...", "/free-rooms", "/cancelled", "/exams"]
    }