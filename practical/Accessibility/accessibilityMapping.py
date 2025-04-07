import re
import json
import os

# The json is used to map the htmlcodesniffer issues to the axe-core issues
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
CSANDAXEMAPPER_JSON_PATH = os.path.join(DIR_PATH, 'mappingCsAndAxeCore.json')


'''
    This module is used to map the issues found by different accessibility testing tools
    to one common format.
    Since the tools use either the wcag id (e.g. wcag2a 1.1.1) or the url to the wcag page
    (e.g. https://dequeuniversity.com/rules/axe/4.10/aria-meter-name), we need to map them 
    based on both the id and the url.
'''

# update amount to get the maximum of pa11y, axe-core and lighthouse per 
def update_amount(wcag_issues_dict):
    wcag_issues_dict_clone = wcag_issues_dict.copy()

    for key, issues_list in wcag_issues_dict.items():
        old_htmlcs_id, old_axe_url, old_impact, amount = key

        amount_pa11y_issues = 0
        amount_axe_issues = 0
        amount_lighthouse_issues = 0

        for issue in issues_list:
            if issue["source"] == "pa11y":
                amount_pa11y_issues += 1
            elif issue["source"] == "axe-core":
                amount_axe_issues += 1
            elif issue["source"] == "lighthouse":
                amount_lighthouse_issues += 1

        amount_max = max(amount_pa11y_issues, amount_axe_issues, amount_lighthouse_issues)

        # Update existing amounts
        issues_list = wcag_issues_dict_clone.pop(key) 
        wcag_issues_dict_clone[(old_htmlcs_id, old_axe_url, old_impact, amount_max)] = issues_list

    return wcag_issues_dict_clone


# Convert it to json readable format
def prepare_wcag_issues_json(wcag_issues_dict):
    output = []

    for (wcag_id, url, impact, amount), issues_list in wcag_issues_dict.items():
        item = {
            "wcag_id": wcag_id,
            "url": url,
            "impact": impact,
            "amount": amount,
            "issues": issues_list
        }
        output.append(item)

    return output


def map_htmlcsniffer_and_axecore(id, htmlcsniffer=True):
    with open(CSANDAXEMAPPER_JSON_PATH, "r") as f:
        cs_and_axe_mapping = json.load(f)

    # Check if the id is in the mapping
    if htmlcsniffer:
        for mapping in cs_and_axe_mapping:
            htmlcs_id = mapping["htmlcs_id"]
            axe_url = mapping["axe_url"]
            impact = mapping["impact"]
                
            if htmlcs_id == id and id is not None:
                return htmlcs_id, axe_url, impact
                
        # if no htmlcs_id entry in cs_and_axe_mapping corresponds to this issue, then return "tbd"
        return id, None, "to be defined"
    
    if not htmlcsniffer:
        for mapping in cs_and_axe_mapping:
            htmlcs_id = mapping["htmlcs_id"]
            axe_url = mapping["axe_url"]
            impact = mapping["impact"]

            if axe_url == id and id is not None:
                return htmlcs_id, axe_url, impact
                
        # if no axe_url entry in cs_and_axe_mapping corresponds to this issue, then return "tbd"
        return None, id, "to be defined"


# Pa11y only shows the wcag id, but not the url
def pa11y_mapping(issues, wcag_issues_dict):
    # Load the json file
    for issue in issues:
        issue_id = issue["code"].split("WCAG2AA.")[1]

        htmlcs_id, axe_url, impact = map_htmlcsniffer_and_axecore(issue_id, True)

        full_issue = {
            "id": issue.get("code", ""),
            "source": "pa11y",
            "title": issue.get("message", ""),
            "description": issue.get("context", ""),
            "impact": issue.get("type", ""),
            "original_issue": issue
        }


        found = False
        for key, issues_list in wcag_issues_dict.items():
            existing_wcag_id, existing_url, existing_impact, existing_amount = key
            if htmlcs_id == existing_wcag_id:
                issues_list.append(full_issue)
                found = True
                break
        
        # if no match found, create new entry
        if not found:
            wcag_issues_dict[(htmlcs_id, axe_url, impact, 1)] = [full_issue]


# Axe-core shows the url and wcag id
def axe_core_mapping(issues, wcag_issues_dict):
    for issue in issues:
        issue_url = issue["helpUrl"].split("?")[0]

        htmlcs_id, axe_url, impact = map_htmlcsniffer_and_axecore(issue_url, False)

        
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
        
        found = False
        for key, issues_list in wcag_issues_dict.items():
            existing_wcag_id, existing_url, impact, amount = key
            if (htmlcs_id is not None and htmlcs_id == existing_wcag_id) or (axe_url == existing_url):
                issues_list.append(full_issue)
                found = True

                break

        # if no match found, create new entry
        if not found:
            wcag_issues_dict[(None, axe_url, impact, 1)] = [full_issue]


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

            htmlcs_id, axe_url, impact = map_htmlcsniffer_and_axecore(issue_url, False)


            found = False
            for key, issues_list in wcag_issues_dict.items():
                existing_wcag_id, existing_url, impact, amount = key
                if axe_url == existing_url:
                    issues_list.append({
                        "id": issue_id,
                        "source": "lighthouse",
                        "title": issue_data.get("title", ""),
                        "description": description,
                        "score": issue_data.get("score"),
                        "details": issue_data.get("details", {})
                    })

                    found = True
                    break
            
            # if no match found, create new entry
            if not found:
                wcag_issues_dict[(htmlcs_id, axe_url, impact, 1)] = [{
                    "id": issue_id,
                    "source": "lighthouse",
                    "title": issue_data.get("title", ""),
                    "description": description,
                    "score": issue_data.get("score"),
                    "details": issue_data.get("details", {})
                }]
        
        # Use other entry if no url found
        else:
            if ("Other", "Other", "Other", 0) in wcag_issues_dict:
                wcag_issues_dict[("Other", "Other", "Other", 0)].append({
                    "id": issue_id,
                    "source": "lighthouse",
                    "title": issue_data.get("title", ""),
                    "description": description,
                    "score": issue_data.get("score"),
                    "details": issue_data.get("details", {})
                })
            else:
                wcag_issues_dict[("Other", "Other", "Other", 0)] = [{
                    "id": issue_id,
                    "source": "lighthouse",
                    "title": issue_data.get("title", ""),
                    "description": description,
                    "score": issue_data.get("score"),
                    "details": issue_data.get("details", {})
                }]



# Main function to call all mappings
def full_matching(pa11y, axe_core, lighthouse):
    wcag_issues_dict = {}

    pa11y_mapping(pa11y, wcag_issues_dict)
    axe_core_mapping(axe_core, wcag_issues_dict)
    lighthouse_mapping(lighthouse, wcag_issues_dict)

    wcag_issues_dict = update_amount(wcag_issues_dict)

    wcag_issues_dict = prepare_wcag_issues_json(wcag_issues_dict)

    return wcag_issues_dict
    

