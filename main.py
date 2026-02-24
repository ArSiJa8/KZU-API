import os
import time
import requests
import datetime
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv

# Lädt INTRANET_USER und INTRANET_PW aus der .env oder Railway
load_dotenv()

app = FastAPI(title="KZU All-Data API")

USER = os.getenv("INTRANET_USER")
PW = os.getenv("INTRANET_PW")
BASE_URL = "https://intranet.tam.ch/kzu"

def fetch_raw_kzu_data():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'X-Requested-With': 'XMLHttpRequest'
    })

    # 1. Login
    login_payload = {
        'loginschool': 'kzu',
        'loginuser': USER,
        'loginpassword': PW
    }
    session.post(BASE_URL, data=login_payload)

    if 'sturmsession' not in session.cookies:
        raise HTTPException(status_code=401, detail="Login fehlgeschlagen. Variablen prüfen!")

    # 2. Zeitfenster setzen
    # Start: Heute / Ende: In 7 Tagen
    start_ts = int(time.time() * 1000)
    end_ts = start_ts + (7 * 24 * 60 * 60 * 1000)

    # 3. Request für alle Daten
    # Laut deiner Datei braucht der Server die startDate/endDate und classId[]
    ajax_url = f"{BASE_URL}/timetable/ajax-get-timetable"

    # Wenn wir keine spezifische classId mitschicken, liefert das Intranet
    # oft die Daten für den eigenen Account/alle Klassen.
    # Wir schicken classId[] leer mit oder lassen es weg.
    payload = {
        'startDate': start_ts,
        'endDate': end_ts,
        'holidaysOnly': 0
    }

    response = session.post(ajax_url, data=payload)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Intranet Server Fehler")

    return response.json()

@app.get("/api/all")
def get_all():
    """Gibt den kompletten Datensatz zurück, wie in deiner output.txt"""
    return fetch_raw_kzu_data()

@app.get("/")
def home():
    return {"status": "online", "docs": "/docs"}