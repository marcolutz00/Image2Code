import os
import re

'''
    Due to the design of the Datasets which we are using, the <a> in each Data Entry
    does not contain a href attribute.
    This leads to problems concerning some Wcag Standards.
    In order to solve those issues by design, we are going to add an empty href="#" 
    for each <a>
'''

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
HTML_PATH= os.path.join(DIR_PATH, '..', 'Input', 'html')
HTML_PATH_ADJUSTED = os.path.join(DIR_PATH, '..', 'Input', 'html', 'adjusted')

# Regex whcich checks if already a href attribute exists or not.
# If not, add an empty attribute
def add_empty_href(html):
    return re.sub(r'(<a\b)(?![^>]*\bhref\s*=)', r'\1 href="#"', html, flags=re.IGNORECASE)


def start():
    for file in os.listdir(HTML_PATH):
        if os.path.isdir(os.path.join(HTML_PATH, file)):
            continue

        with open(os.path.join(HTML_PATH, file), 'r', encoding='utf-8') as f:
            html = f.read()
        
        adjusted_html = add_empty_href(html)

        with open(os.path.join(HTML_PATH_ADJUSTED, file), 'w', encoding='utf-8') as w:
            w.write(adjusted_html)
        

if __name__ == "__main__":
    start()