from difflib import SequenceMatcher
from bs4 import BeautifulSoup


def _clean_html(text):
    '''
        Clean HTML text
    '''
    # remove whitespace and linebreaks
    text = text.split()
    text = ' '.join(text)

    # to lowercase
    text = text.lower()

    return text


def _get_text_from_html(html_path):
    '''
        Find only text in HTML (incl. some cleaning)
    '''
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    
    # delete all unneccaesary tags
    for elem in soup(["meta", "script", "style"]):
        elem.decompose()  

    text = soup.get_text()

    clean_text = _clean_html(text)

    return clean_text


def text_similarity_score(html1_path, html2_path):
    '''
        Calculation of similarity with SequenceMatcher
    '''

    text1 = _get_text_from_html(html1_path)
    text2 = _get_text_from_html(html2_path)

    seq_match = SequenceMatcher(None, text1, text2)

    score = seq_match.ratio()

    return score


