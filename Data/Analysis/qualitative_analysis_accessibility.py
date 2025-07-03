from bs4 import BeautifulSoup as bs
import os
from pathlib import Path
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import Utils.utils_dataset as utils_dataset


def is_class_relevant(class_name):
    """
    Check if the class name relevant
    """
    important_class_substrings = ["header", "footer", "nav", "main", "aside", "sidebar", "section"]
    return any(substring in class_name for substring in important_class_substrings)

def extract_elements_after_body(map_findings, html_path):
    """
    Which elements come after the <body> tag in the HTML file?
    """

    with open(html_path, 'r', encoding='utf-8') as f:
        soup = bs(f.read(), 'html.parser')

    body_soup = soup.find('body')
    landmarks_found = False
    relevant_div_found = False
    container_found = False

    if body_soup is None:
        map_findings["no_body"] = map_findings.get("no_body", 0) + 1
    
    elements_after = []
    for element in body_soup.find_all(recursive=False):
        # All landmark elements
        if element.name == 'main':
            map_findings["main"] = map_findings.get("main", 0) + 1
            landmarks_found = True
        elif element.name == 'header':
            map_findings["header"] = map_findings.get("header", 0) + 1
            landmarks_found = True
        elif element.name == 'footer':
            map_findings["footer"] = map_findings.get("footer", 0) + 1
            landmarks_found = True
        elif element.name == 'nav':
            map_findings["nav"] = map_findings.get("nav", 0) + 1
            landmarks_found = True
        elif element.name == 'aside':
            map_findings["aside"] = map_findings.get("aside", 0) + 1
            landmarks_found = True
        elif element.name == 'section':
            map_findings["section"] = map_findings.get("section", 0) + 1
            landmarks_found = True
        
        # if div then get the class
        elif element.name == 'div' and not landmarks_found:
            
            classes = element.get('class', [])
            if classes:
                for unique_class in classes:
                    # if class name == "container" then check divs below
                    if unique_class == "container":
                        container_found = True
                        for sub_div in element.find_all('div', recursive=False):
                            sub_div_class = sub_div.get('class', [])
                            if sub_div_class:
                                found = False
                                if is_class_relevant(sub_div_class[0]):
                                    key = f'div.container.{sub_div_class[0]}'
                                    map_findings[key] = map_findings.get(key, 0) + 1
                                    found = True

                                if not found:
                                    map_findings['div.container_notrelevant'] = map_findings.get('div.container_notrelevant', 0) + 1

                    elif is_class_relevant(unique_class):
                        relevant_div_found = True
                        key = f'div.{unique_class}'
                        map_findings[key] = map_findings.get(key, 0) + 1
                    else:
                        map_findings['div_notrelevant'] = map_findings.get('div_notrelevant', 0) + 1

    if landmarks_found:
        map_findings["a_landmarks"] = map_findings.get("a_landmarks", 0) + 1
    elif container_found and not relevant_div_found:
        map_findings['a_div.container'] = map_findings.get('a_div.container', 0) + 1
    elif not container_found and relevant_div_found:
        map_findings['a_div.relevant'] = map_findings.get('a_div.relevant', 0) + 1
    elif relevant_div_found and container_found:
        map_findings['a_div.container_relevant'] = map_findings.get('a_div.container_relevant', 0) + 1
    elif not landmarks_found and not container_found:
        map_findings["a_no_landmarks"] = map_findings.get("a_no_landmarks", 0) + 1




def start_qualitative_analysis(list_paths):
    """
    Start qualitative analysis
    """

    map_findings = {}

    for name, path in list_paths.items():
        html_files = [f for f in utils_dataset.sorted_alphanumeric(os.listdir(path)) if f.endswith('.html')]

        print(f"{len(html_files)} HTML files")

        for file in html_files:
            html_path = os.path.join(path, file)
            extract_elements_after_body(map_findings, html_path)

    return map_findings

if __name__ == "__main__":
    curr_path = Path(__file__).parent

    list_paths = {
        "gemini_naive_1": curr_path.parent / "Output" / "gemini" / "html" / "naive" / "2025-06-18-10-18",
        "gemini_naive_2": curr_path.parent / "Output" / "gemini" / "html" / "naive" / "2025-06-18-11-24",
        "gemini_naive_3": curr_path.parent / "Output" / "gemini" / "html" / "naive" / "2025-06-18-11-53",
        "gemini_few_shot_1": curr_path.parent / "Output" / "gemini" / "html" / "few-shot" / "2025-06-29-09-55",
        "gemini_few_shot_2": curr_path.parent / "Output" / "gemini" / "html" / "few-shot" / "2025-06-29-10-41",
        "gemini_few_shot_3": curr_path.parent / "Output" / "gemini" / "html" / "few-shot" / "2025-06-29-11-21",
        "gemini_zero_shot_1": curr_path.parent / "Output" / "gemini" / "html" / "zero-shot" / "2025-06-18-13-25",
        "gemini_zero_shot_2": curr_path.parent / "Output" / "gemini" / "html" / "zero-shot" / "2025-06-18-14-29",
        "gemini_zero_shot_3": curr_path.parent / "Output" / "gemini" / "html" / "zero-shot" / "2025-06-18-15-40",
        "gemini_reason_1": curr_path.parent / "Output" / "gemini" / "html" / "reason" / "2025-06-18-16-24",
        "gemini_reason_2": curr_path.parent / "Output" / "gemini" / "html" / "reason" / "2025-06-18-17-38",
        "gemini_reason_3": curr_path.parent / "Output" / "gemini" / "html" / "reason" / "2025-06-18-20-49",
        
        "openai_naive_1": curr_path.parent / "Output" / "openai" / "html" / "naive" / "2025-06-19-15-41",
        "openai_naive_2": curr_path.parent / "Output" / "openai" / "html" / "naive" / "2025-06-19-16-53",
        "openai_naive_3": curr_path.parent / "Output" / "openai" / "html" / "naive" / "2025-06-19-19-05",
        "openai_few_shot_1": curr_path.parent / "Output" / "openai" / "html" / "few-shot" / "2025-06-30-20-08",
        "openai_few_shot_2": curr_path.parent / "Output" / "openai" / "html" / "few-shot" / "2025-06-30-20-39",
        "openai_few_shot_3": curr_path.parent / "Output" / "openai" / "html" / "few-shot" / "2025-06-30-21-49",
        "openai_zero_shot_1": curr_path.parent / "Output" / "openai" / "html" / "zero-shot" / "2025-06-20-09-55",
        "openai_zero_shot_2": curr_path.parent / "Output" / "openai" / "html" / "zero-shot" / "2025-06-20-11-10",
        "openai_zero_shot_3": curr_path.parent / "Output" / "openai" / "html" / "zero-shot" / "2025-06-20-12-33",
        "openai_reason_1": curr_path.parent / "Output" / "openai" / "html" / "reason" / "2025-06-20-15-39",
        "openai_reason_2": curr_path.parent / "Output" / "openai" / "html" / "reason" / "2025-06-20-17-42",
        "openai_reason_3": curr_path.parent / "Output" / "openai" / "html" / "reason" / "2025-06-20-19-43",
    }

    findings = start_qualitative_analysis(list_paths)
    print(findings)