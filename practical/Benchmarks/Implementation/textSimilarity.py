from difflib import SequenceMatcher
from bs4 import BeautifulSoup
import os

DIR_PATH = os.path.join(os.path.dirname(__file__))
# For tests
DATA_PATH = os.path.join(DIR_PATH, '..', '..', 'Data')
INPUT_HTML_PATH = os.path.join(DATA_PATH, 'Input', 'html')
OUTPUT_HTML_PATH = os.path.join(DATA_PATH, 'Output', 'openai', 'html')


'''
    Find only text in HTML (incl. some cleaning)
'''
def get_text_from_html(html_path):
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    
    # delete all unneccaesary tags
    for elem in soup(["meta", "script", "style"]):
        elem.decompose()  

    text = soup.get_text()

    # remove all newlines and tabs
    text = text.split()
    text = ' '.join(text)

    return text



# Calculation of similarity with SequenceMatcher
def text_similarity_score(code1, code2):
    text1 = get_text_from_html(code1)
    text2 = get_text_from_html(code1)

    seq_match = SequenceMatcher(None, text1, text2)

    score = seq_match.ratio()

    return score




# Tests
# html_original = f"{INPUT_HTML_PATH}/1.html"
# html_generated = f"{OUTPUT_HTML_PATH}/1.html"

# score = text_similarity_score(html_original, html_generated)
# print(score)

