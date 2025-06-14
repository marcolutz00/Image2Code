import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import Utils.utils_html as utils_html


url = "http://localhost:8000/de/accounts/signup/"
name = "signup.html"

utils_html.extract_html_css_from_website(
    url,
    os.path.join(os.path.dirname(__file__), name),
    store_html=True
)