import re
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from practical.LLMs.LLMClient import LLMClient
from practical.Utils import utils_dataset
from LLMs.Strategies.geminiStrategy import GeminiStrategy
from practical.Accessibility import accessibilityIssues


KEYS_PATH = os.path.join(os.path.dirname(__file__), '..', 'keys.json')
DATASET_HF = "marcolutz/Image2Code"


'''
    This function tries to automatically map the Accessibility issues found 
    by axe-core, lighthouse, pa11y with the help of AI 
    Model used: Gemini-2.0-flash
    
    Goal: 
    Map the issues found by all 3 automatic tools into 
    one JSON. Same issues should not combined.
'''

# Pa11y only shows the wcag id, but not the url
def pa11y_mapping(issues, wcag_issues_dict):
    # Load the json file
    for issue in issues:
        issue_id = issue["code"].split("WCAG2AA.")[1]

        full_issue = {
            "id": issue.get("code", ""),
            "source": "pa11y",
            "title": issue.get("message", ""),
            "description": issue.get("context", ""),
            "impact": issue.get("type", ""),
            "original_issue": issue
        }


        wcag_issues_dict[issue_id] = [full_issue]


# Axe-core shows the url and wcag id
def axe_core_mapping(issues, wcag_issues_dict):
    for issue in issues:
        issue_url = issue["helpUrl"].split("?")[0]
        
        full_issue = {
            "id": issue.get("id", ""),
            "source": "axe-core",
            "title": issue.get("help", ""),
            "description": issue.get("description", ""),
            "impact": issue.get("impact", ""),
            "helpUrl": issue.get("helpUrl", ""),
            "nodes": issue.get("nodes", []),
            "original_issue": issue
        }
        
        wcag_issues_dict[issue_url] = [full_issue]


# Lighthouse only shows the url
def lighthouse_mapping(issues, wcag_issues_dict):
    for issue_id, issue_data in issues.items():
        # Skip if scoreDisplayMode is null since lighthouse shows all
        if issue_data.get("scoreDisplayMode") in ["notApplicable", "manual"]:
            continue

        # Skip if score = 1 , since then lighthouse is correct
        if issue_data.get("score") == 1:
            continue

        if "description" not in issue_data:
            continue

        description = issue_data["description"]

        # use regex to find url in description
        url_pattern = re.compile(r'\[.*?\]\((https?://[^\s\)]+)\)')
        url_match = url_pattern.search(description)

        if url_match:
            issue_url = url_match.group(1)
            issue_url = issue_url.split("?")[0]


            wcag_issues_dict[issue_url] = [{
                "id": issue_id,
                "source": "lighthouse",
                "title": issue_data.get("title", ""),
                "description": description,
                "score": issue_data.get("score"),
                "details": issue_data.get("details", {})
            }]
        

async def api_matching_ai(issues_dict, current_map):
    # Define prompt
    with open(os.path.join(os.path.dirname(__file__), 'prompt_mapping.txt')) as r:
        prompt = r.read()

    # Load api keys
    with open(KEYS_PATH) as f:
        keys = json.load(f)
        api_key = keys["gemini"]["api_key"]
    
    strategy = GeminiStrategy(api_key=api_key)
    llm_client = LLMClient(strategy)

    return await llm_client.generate_accessibility_matching(prompt, current_map, issues_dict)


def filter_map(generated_map):
    pattern = r"```json\s*(.*?)\s*```"
    match = re.search(pattern, generated_map, re.DOTALL)

    if match: 
        json_str = match.group(1).strip()

        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return None


# Main function to call all mappings
async def full_matching_automatically(pa11y, axe_core, lighthouse):
    wcag_issues_dict = {}

    pa11y_mapping(pa11y, wcag_issues_dict)
    axe_core_mapping(axe_core, wcag_issues_dict)
    lighthouse_mapping(lighthouse, wcag_issues_dict)

    with open(os.path.join(os.path.dirname(__file__), 'mappingCsAndAxeCore_automatically.json')) as f:
        current_map = json.load(f)

    new_generated_map = await api_matching_ai(wcag_issues_dict, current_map)
    new_generated_map = filter_map(new_generated_map)

    # Check if after filter = None
    assert new_generated_map != None

    with open(os.path.join(os.path.dirname(__file__), 'mappingCsAndAxeCore_automatically.json'), 'w', encoding='utf-8') as f:
        json.dump(new_generated_map, f, ensure_ascii=False, indent=4)

    return new_generated_map
    