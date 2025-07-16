import json
import os
from bs4 import BeautifulSoup as bs
import pandas as pd
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import Utils.utils_iterative_prompt as utils_iterative_prompt
import Utils.utils_general as utils_general
import Utils.utils_html as utils_html

PRACTICAL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
CSANDAXEMAPPER_JSON_PATH = os.path.join(PRACTICAL, "Accessibility", 'mappingCsAndAxeCore.json')
mapping_violations = utils_general.read_json(CSANDAXEMAPPER_JSON_PATH)

def _unit_accessibility_violations(violation_id):
    """
    Get the name which units the violations
    """
    
    for mapping in mapping_violations:
        htmlcs_ids = mapping["htmlcs_id"]
        axe_urls = mapping["axe_url"]
        impact = mapping["impact"]
        name = mapping["name"]

        for htmlcs_id in htmlcs_ids:
            if htmlcs_id == violation_id and violation_id is not None:
                return name
        
        for axe_url in axe_urls:
            if axe_url == violation_id and violation_id is not None:
                return name


def _flatten_violations_dict(violations):
    """
    Flatten dict to get simple difference
    """
    seen = set()
    for violation in violations:
        snippet = violation["snippet"]
        rule = violation["id"]

        name = _unit_accessibility_violations(rule)

        text = bs(snippet, "html.parser").get_text(strip=True)
        if text:
            seen.add((text, name))
            continue

        seen.add((snippet, name))
        
    return seen



def calculate_differences_iterative_rounds(accessibility_json1_path: dict, accessibility_json2_path: dict):
    """
    Calculate the differences between iterative rounds
    """
    accessibility_json1 = utils_general.read_json(accessibility_json1_path)
    violations1 = utils_iterative_prompt.extract_issues_tools(accessibility_json1)
    if len(violations1) == 0:
        return None

    accessibility_json2 = utils_general.read_json(accessibility_json2_path)
    violations2 = utils_iterative_prompt.extract_issues_tools(accessibility_json2)

    violations1_flat = _flatten_violations_dict(violations1)
    violations2_flat = _flatten_violations_dict(violations2)

    added = violations2_flat - violations1_flat
    removed = violations1_flat - violations2_flat
    unchanged = violations1_flat & violations2_flat

    df_data = {
        "added": [],
        "removed": [],
        "unchanged": []
    }
    for snippet in added:
        df_data["added"].append({
            "comparison": f"{accessibility_json1_path}_{accessibility_json2_path}",
            "snippet": snippet[0],
            "rule": snippet[1]
        })
    for snippet in removed:
        df_data["removed"].append({
            "comparison": f"{accessibility_json1_path}_{accessibility_json2_path}",
            "snippet": snippet[0],
            "rule": snippet[1]
        })
    for snippet in unchanged:
        df_data["unchanged"].append({
            "comparison": f"{accessibility_json1_path}_{accessibility_json2_path}",
            "snippet": snippet[0],
            "rule": snippet[1]
        })


    return df_data

            