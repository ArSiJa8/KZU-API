import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from fastapi import FastAPI, HTTPException

load_dotenv()

app = FastAPI()

USER = os.getenv("INTRANET_USER")
PW = os.getenv("INTRANET_PW")
URL = os.getenv("BASE_URL")

def scrape_intranet():
    if not USER or not PW:
        raise ValueError("Logindaten fehlen in den Umgebungsvariablen!")

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            page.goto(URL)

            page.fill('input[name="username"]', USER)
            page.fill('input[name="password"]', PW)
            page.click('button[type="submit"]')

            page.wait_for_load_state("networkidle")
            

            info_element = page.query_selector(".content-area") 
            data = info_element.inner_text() if info_element else "Keine Daten gefunden"
            
            return {"status": "success", "content": data}
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
        finally:
            browser.close()

@app.get("/api/data")
def get_data():
    result = scrape_intranet()
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result
