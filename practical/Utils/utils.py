from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import os
from pathlib import Path
import json

# Load Keys
def load_keys(company):
    config_path = Path(__file__).resolve().parent.parent / "keys.json"
        
    with open(config_path, "r", encoding="utf-8") as f:
        keys_json = json.load(f)

    api_key = keys_json[company]

    return api_key


# API-Call and store code
def save_code(code, file_name="generated_code.html"):
    # Store as HTML
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(code)
    print(f"Code gespeichert als {file_name}")


# Check first if any compiler errors
def validate_html(generatedHtml_path):
    # check if mistakes
    try:
        soup = BeautifulSoup(generatedHtml_path, "html.parser")
        return True
    except Exception as e:
        print("HTML error:", e)
        return False


# Rendering the code and doing a screenshot of it afterwards (headless)
def render_and_screenshot(generatedHtml_path, screenshot_path):
    with sync_playwright() as playwright:
        chromium = playwright.chromium # oder "firefox" oder "webkit".
        browser = chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(generatedHtml_path)
        page.screenshot(path=screenshot_path)
        browser.close()

    print(f"Screenshot saved in {screenshot_path}")



