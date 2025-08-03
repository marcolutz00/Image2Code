import json
from bs4 import BeautifulSoup as bs
import os 
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import Data.Analysis.qualitative_analysis.landmarks as landmarks
import Data.Analysis.qualitative_analysis.stats as stats

def _count_dom_nodes(soup) -> int:
    return len(soup.find_all())


def _soupify_html(html_path):
    """
    Load HTML file in bs4
    """
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = bs(f.read(), 'html.parser')
    return soup


def get_complexity_structure(map_findings, html_path, model_name):
    """
    returs the amount of dom-nodes in the html file
    """
    soup = _soupify_html(html_path)
    amount_nodes = _count_dom_nodes(soup)

    if map_findings.get(model_name) is None:
        map_findings[model_name] = []
    map_findings[model_name].append(amount_nodes)




# Hypothesis Landmarks: Less complex structures have more landmark violations
def estimate_complexity_structure(list_findings, html_path, model_name):
    """
    Complexity based on number of dom-elements
    """
    accessibility_path = html_path.replace(".html", ".json")
    accessibility_path = accessibility_path.replace("html", "accessibility")

    with open(accessibility_path, 'r', encoding='utf-8') as f:
        accessibility_data = json.load(f)

    amount_landmark_violations = stats.get_all_violations(accessibility_data, "Landmark & Region; Missing & Unique Landmarks;")

    soup = _soupify_html(html_path)
    
    nodes_amount = _count_dom_nodes(soup)

    list_findings.append({
        "model": model_name,
        "html_path": html_path,
        "amount_landmark_violations": amount_landmark_violations,
        "amount_nodes": nodes_amount
    })


# Hypothesis : Dataset 2 is more complex than dataset 1, thus causing more violations and less equal distributed across models
def estimate_complexity_datasets(map_complexity, html_path, model_name):
    """
    Estimate complexity of datasets
    """
    # 28. entry is the cut for dataset 1 (design2Code) and 2 (webcode2m)
    dataset_cut = 28

    file_name = int(html_path.split("/")[-1].replace(".html", ""))

    soup = _soupify_html(html_path)
    nodes_amount = _count_dom_nodes(soup)

    if file_name <= dataset_cut:
        dataset = "design2Code"
    else:
        dataset = "webcode2m"

    if map_complexity.get(dataset) is None:
        map_complexity[dataset] = {}

    if map_complexity[dataset].get(model_name) is None:
        map_complexity[dataset][model_name] = {
            "amount_nodes": [],
            "mean_nodes": 0
        }

    map_complexity[dataset][model_name]["amount_nodes"].append(nodes_amount)
    map_complexity[dataset][model_name]["mean_nodes"] = sum(map_complexity[dataset][model_name]["amount_nodes"]) / len(map_complexity[dataset][model_name]["amount_nodes"])


