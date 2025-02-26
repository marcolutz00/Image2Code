from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import os

# Check first if any compiler errors
def validate_html(html_code):
    # check if mistakes
    try:
        soup = BeautifulSoup(html_code, "html.parser")
        return True
    except Exception as e:
        print("HTML error:", e)
        return False


# Rendering the code
