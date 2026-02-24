from playwright.sync_api import sync_playwright
from fastapi import FastAPI

app = FastAPI()

def scrape_intranet():
    with sync_playwright() as p:
        # Browser starten (headless auf dem Server)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Login-Seite aufrufen
        page.goto("https://intranet.tam.ch/kzu")
        
        # Login-Daten eingeben (Selektoren müssen im HTML geprüft werden)
        page.fill('input[name="username"]', "DEIN_USER")
        page.fill('input[name="password"]', "DEIN_PASSWORT")
        page.click('button[type="submit"]')
        
        # Warten, bis die Daten geladen sind
        page.wait_for_selector(".daten-container")
        
        # Daten extrahieren
        data = page.inner_text(".relevante-info")
        
        browser.close()
        return {"data": data}

@app.get("/get-info")
def get_info():
    return scrape_intranet()
