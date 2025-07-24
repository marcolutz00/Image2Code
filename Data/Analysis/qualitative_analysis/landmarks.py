from bs4 import BeautifulSoup as bs


def _is_class_relevant(class_name):
    """
    Check if the class name relevant
    """
    important_class_substrings = ["header", "footer", "nav", "main", "aside", "sidebar", "section"]
    return any(substring in class_name for substring in important_class_substrings)


# Hypothesis Landmarks: The basic structure of landmakrs does exist, however not implemented with landmark tags
def check_elements_after_body(map_findings, html_path, model_name):
    """
    Which elements come after the <body> tag in the HTML file?
    """
    if map_findings.get(model_name) is None:
        map_findings[model_name] = {}

    with open(html_path, 'r', encoding='utf-8') as f:
        soup = bs(f.read(), 'html.parser')

    body_soup = soup.find('body')
    landmarks_found = False
    relevant_div_found = False
    container_found = False

    if body_soup is None:
        map_findings[model_name]["no_body"] = map_findings[model_name].get("no_body", 0) + 1
        return
    
    for element in body_soup.find_all(recursive=False):
        # All landmark elements
        if element.name == 'main':
            map_findings[model_name]["main"] = map_findings[model_name].get("main", 0) + 1
            landmarks_found = True
        elif element.name == 'header':
            map_findings[model_name]["header"] = map_findings[model_name].get("header", 0) + 1
            landmarks_found = True
        elif element.name == 'footer':
            map_findings[model_name]["footer"] = map_findings[model_name].get("footer", 0) + 1
            landmarks_found = True
        elif element.name == 'nav':
            map_findings[model_name]["nav"] = map_findings[model_name].get("nav", 0) + 1
            landmarks_found = True
        elif element.name == 'aside':
            map_findings[model_name]["aside"] = map_findings[model_name].get("aside", 0) + 1
            landmarks_found = True
        elif element.name == 'section':
            map_findings[model_name]["section"] = map_findings[model_name].get("section", 0) + 1
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
                                if _is_class_relevant(sub_div_class[0]):
                                    key = f'div.container.{sub_div_class[0]}'
                                    map_findings[model_name][key] = map_findings[model_name].get(key, 0) + 1
                                    found = True

                                if not found:
                                    map_findings[model_name]['div.container_notrelevant'] = map_findings[model_name].get('div.container_notrelevant', 0) + 1

                    elif _is_class_relevant(unique_class):
                        relevant_div_found = True
                        key = f'div.{unique_class}'
                        map_findings[model_name][key] = map_findings[model_name].get(key, 0) + 1
                    else:
                        map_findings[model_name]['div_notrelevant'] = map_findings[model_name].get('div_notrelevant', 0) + 1

    if landmarks_found:
        map_findings[model_name]["a_landmarks"] = map_findings[model_name].get("a_landmarks", 0) + 1
    elif container_found and not relevant_div_found:
        map_findings[model_name]['a_div.container'] = map_findings[model_name].get('a_div.container', 0) + 1
    elif not container_found and relevant_div_found:
        map_findings[model_name]['a_div.relevant'] = map_findings[model_name].get('a_div.relevant', 0) + 1
    elif relevant_div_found and container_found:
        map_findings[model_name]['a_div.container_relevant'] = map_findings[model_name].get('a_div.container_relevant', 0) + 1
    elif not landmarks_found and not container_found:
        map_findings[model_name]["a_no_landmarks"] = map_findings[model_name].get("a_no_landmarks", 0) + 1



