import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import Utils.utils_html as utils_html



for html_file in os.listdir(os.path.dirname(__file__)):
    if html_file.endswith(".html"):
        with open(os.path.join(os.path.dirname(__file__), html_file), "r", encoding="utf-8") as f:
            html = f.read()
        
        html_clean = utils_html.change_links_and_img(html)

        with open(os.path.join(os.path.dirname(__file__), "cleaned_" + html_file), "w", encoding="utf-8") as f:
            f.write(html_clean)