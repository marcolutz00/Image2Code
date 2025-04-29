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
        old_htmlcs_id, old_axe_url, old_impact, amount, old_name = key

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
        wcag_issues_dict_clone[(old_htmlcs_id, old_axe_url, old_impact, amount_max, old_name)] = issues_list

    return wcag_issues_dict_clone


# Convert it to json readable format
def prepare_wcag_issues_json(wcag_issues_dict, total_nodes_checked, lighthouse_accessibility_score):
    issues = []

    total_nodes_failed = 0
    for (wcag_id, url, impact, amount, name), issues_list in wcag_issues_dict.items():
        item = {
            "wcag_id": wcag_id,
            "url": url,
            "impact": impact,
            "name": name,
            "amount_nodes_failed": amount,
            "issues": issues_list
        }
        total_nodes_failed += amount
        issues.append(item)
    
    automatic_results = {
        "lighthouse_accessibility_score": lighthouse_accessibility_score,
        "total_nodes_checked": total_nodes_checked,
        "total_nodes_failed": total_nodes_failed,
    }

    manual_results = {
        "total_SC": "8",
        "failed_SC": "to be defined",
        "details": {
            "1.4.4": "tbd",
            "1.4.10": "tbd",
            "1.4.11": "tbd",
            "1.4.12": "tbd",
            "2.1.1 + 2.1.2": "tbd",
            "2.4.3": "tbd",
            "2.4.6": "tbd",
            "2.4.7": "tbd",
        }
    }

    # TODO: Overall Status definieren (ROT, GRÜN, GELB, ...)
    output = {
        "automatic": automatic_results,
        "manual": manual_results,
        "overall_status": "to be defined",
        "issues": issues
    }

    return output


def map_htmlcsniffer_and_axecore(id, htmlcsniffer=True):
    with open(CSANDAXEMAPPER_JSON_PATH, "r") as f:
        cs_and_axe_mapping = json.load(f)

    for mapping in cs_and_axe_mapping:
        htmlcs_ids = mapping["htmlcs_id"]
        axe_urls = mapping["axe_url"]
        impact = mapping["impact"]
        name = mapping["name"]

        # Check if the id is in the mapping
        if htmlcsniffer:
            for htmlcs_id in htmlcs_ids:
                if htmlcs_id == id and id is not None:
                    return htmlcs_ids, axe_urls, impact, name
        
        else:
            for axe_url in axe_urls:
                if axe_url == id and id is not None:
                    return htmlcs_ids, axe_urls, impact, name
                    

    
    if htmlcsniffer:
        # if no htmlcs_id entry in cs_and_axe_mapping corresponds to this issue, then return "tbd"
        return id, None, "to be defined", "to be defined"
    else:
        # if no axe_url entry in cs_and_axe_mapping corresponds to this issue, then return "tbd"
        return None, id, "to be defined", "to be defined"


# Pa11y only shows the wcag id, but not the url
def pa11y_mapping(issues, wcag_issues_dict):
    # Load the json file
    for issue in issues:
        issue_id = issue["code"].split("WCAG2AA.")[1]

        htmlcs_id, axe_url, impact, name = map_htmlcsniffer_and_axecore(issue_id, True)
        htmlcs_id_tuple = tuple(htmlcs_id) if isinstance(htmlcs_id, list) else htmlcs_id
        
        full_issue = {
            "id": issue_id,
            "source": "pa11y",
            "title": issue.get("message", ""),
            "description": issue.get("context", ""),
            "impact": issue.get("type", ""),
            "original_issue": issue
        }


        found = False
        for key, issues_list in list(wcag_issues_dict.items()):
            existing_wcag_id, existing_url, existing_impact, existing_amount, existing_name = key
            if htmlcs_id_tuple == existing_wcag_id:
                issues_list.append(full_issue)
                found = True
                break
        
        # if no match found, create new entry
        if not found:
            axe_url_tuple = tuple(axe_url) if isinstance(axe_url, list) else axe_url
            wcag_issues_dict[(htmlcs_id_tuple, axe_url_tuple, impact, 1, name)] = [full_issue]


# Axe-core shows the url and wcag id of all the violations
def axe_core_mapping(issues, wcag_issues_dict):
    for issue in issues:
        issue_url = issue["helpUrl"].split("?")[0]

        htmlcs_id, axe_url, impact, name = map_htmlcsniffer_and_axecore(issue_url, False)

        htmlcs_id_tuple = tuple(htmlcs_id) if isinstance(htmlcs_id, list) else htmlcs_id
        axe_url_tuple = tuple(axe_url) if isinstance(axe_url, list) else axe_url


        assert len(issue.get("nodes")) > 0

        for issue_detail in issue.get("nodes", []):
            full_issue = {
                "id": issue_url,
                "source": "axe-core",
                "title": issue.get("help", ""),
                "description": issue.get("description", ""),
                "impact": issue.get("impact", ""),
                "nodes": issue_detail
            }
        
            found = False
            for key, issues_list in list(wcag_issues_dict.items()):
                existing_wcag_id, existing_url, existing_impact, existing_amount, existing_name = key

                # Important: Works only if URL unique in mapping
                if axe_url_tuple == existing_url:
                    issues_list.append(full_issue)
                    found = True

                    break

            # if no match found, create new entry
            if not found:
                wcag_issues_dict[(htmlcs_id_tuple, axe_url_tuple, impact, 1, name)] = [full_issue]


# Calculates the amount of issues which have been tested by Axe-Core
def axe_core_nodes_checked(axe_core_violations, axe_core_incomplete, axe_core_passes):
    amount_nodes_checked = 0

    for issues_per_category in [axe_core_violations, axe_core_incomplete, axe_core_passes]:
        for issue in issues_per_category:
            nodes = issue.get("nodes")
            assert len(nodes) > 0

            amount_nodes_checked += len(nodes)

    return amount_nodes_checked


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

            htmlcs_id, axe_url, impact, name = map_htmlcsniffer_and_axecore(issue_url, False)

            htmlcs_id_tuple = tuple(htmlcs_id) if isinstance(htmlcs_id, list) else htmlcs_id
            axe_url_tuple = tuple(axe_url) if isinstance(axe_url, list) else axe_url

            found = False
            for key, issues_list in list(wcag_issues_dict.items()):
                existing_wcag_id, existing_url, existing_impact, existing_amount, existing_name = key

                assert issue_data.get("details") is not None

                if axe_url_tuple == existing_url:
                    for issue_detail in issue_data.get("details", {}).get("items", []):
                        issues_list.append({
                            "id": issue_url,
                            "source": "lighthouse",
                            "title": issue_data.get("title", ""),
                            "description": description,
                            "score": issue_data.get("score"),
                            "details": issue_detail
                        })

                        found = True

                    break
            
            # if no match found, create new entry
            if not found:
                for issue_detail in issue_data.get("details", {}).get("items", []):
                    wcag_issues_dict[(htmlcs_id_tuple, axe_url_tuple, impact, 1, name)] = [{
                        "id": issue_url,
                        "source": "lighthouse",
                        "title": issue_data.get("title", ""),
                        "description": description,
                        "score": issue_data.get("score"),
                        "details": issue_detail
                    }]



# Main function to call all mappings
def full_matching(pa11y, axe_core, lighthouse):
    '''
        wcag_issues_dict_automatic : contains all automatic found issues which do not require human checking
        wcag_issues_dict_manual : contains all issues which have to be checked manually again
    '''
    wcag_issues_dict_automatic = {}
    wcag_issues_dict_manual = {}

    '''
        1. Axe-Core differentiates in 4 categories:
        passes : rule tested, all elements okay
        violations : rule tested, at least 1 error
        incomplete : rule needs human judgement
        inapplicable : rule can't be tested, since web-page does not contain an element which fits the rule
    '''
    axe_core_violations = axe_core["violations"]
    axe_core_incomplete = axe_core["incomplete"]
    axe_core_passes = axe_core["passes"]
    axe_core_mapping(axe_core_violations, wcag_issues_dict_automatic)
    axe_core_mapping(axe_core_incomplete, wcag_issues_dict_manual)

    # get the amount of nodes which have been checked by axe-core
    total_nodes_checked = axe_core_nodes_checked(axe_core_violations, axe_core_incomplete, axe_core_passes)

    '''
        2. Pa11y only shows errors/violations
    '''
    pa11y_mapping(pa11y, wcag_issues_dict_automatic)


    '''
        3. Lighthouse returns multiple informations
        audits : all WCAG-rules similar to axe-core, however no information about the amount of nodes tested
        categories : Information about categories tested (in this case only "accessibility"). Interesting: Lighthouse releases final score. Can be used as another benchmark
    '''
    lighthouse_audits = lighthouse["audits"]
    lighthouse_accessibility_score = lighthouse["categories"].get("accessibility").get("score")
    lighthouse_mapping(lighthouse_audits, wcag_issues_dict_automatic)

    wcag_issues_dict_automatic = update_amount(wcag_issues_dict_automatic)

    wcag_issues_dict_automatic_json = prepare_wcag_issues_json(wcag_issues_dict_automatic, total_nodes_checked, lighthouse_accessibility_score)


    # TODO: Manual inspection noch hinzufügen.
    return wcag_issues_dict_automatic_json
    

