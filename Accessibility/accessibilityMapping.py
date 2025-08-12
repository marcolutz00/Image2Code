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


def calculate_max_issue_counts(wcag_issues_dict: dict):
    '''
        Updates the amount of issues in the wcag_issues_dict.
        New amount = maximum of pa11y, axe-core and lighthouse
    '''
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



def create_accessibility_report(wcag_issues_dict):
    '''
        Converts the wcag_issues_dict to a json readable format.
    '''
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

    # Manual results have been inspected, however due to the amount of manual inspections and the timeline not possible in this thesis
    manual_results = {
        "checks": {
            "1.4.4": "tbd",
            "1.4.10": "tbd",
            "1.4.12": "tbd",
            "2.1.1+2.1.2": "tbd",
            "2.4.3": "tbd",
            "2.4.6": "tbd",
            "2.4.7": "tbd",
        }
    }

    output = {
        "manual": manual_results,
        "automatic": issues
    }

    return output, total_nodes_failed




def create_overview_report(lighthouse_accessibility_score, total_nodes_checked, total_nodes_failed):
    '''
        Overview Report for the accessibility issues.
        Useful in order to store as json.
    '''

    automatic_results = {
        "lighthouse_accessibility_score": lighthouse_accessibility_score,
        "total_nodes_checked": total_nodes_checked,
        "total_nodes_failed": total_nodes_failed
    }

    manual_results = {
        "total_checks": "tbd",
        "failed_checks": "tbd",
    }

    details_issues = {
    }

    accessibility = {
        "overall_status": "tbd",
        "benchmark": "tbd",
        "automatic_checks": automatic_results,
        "manual_checks": manual_results,
        "details_checks": details_issues
    }


    return accessibility



def map_htmlcsniffer_and_axecore(id: str, htmlcsniffer: bool=True):
    '''
        Maps the found ids from the tools to a common format.
        -> no violations is counted twice
    '''
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
        return id, None, "tbd", "tbd"
    else:
        # if no axe_url entry in cs_and_axe_mapping corresponds to this issue, then return "tbd"
        return None, id, "tbd", "tbd"



def process_pa11y_issues(issues, wcag_issues_dict):
    """
    Pa11y only shows the wcag id, but not the url
    """
    if issues is None or len(issues) == 0:
        return
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



def process_axe_core_issues(issues, wcag_issues_dict):
    """
    Axe-core shows the url and wcag id of all the violations
    """
    if issues is None or len(issues) == 0:
        return
    
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



def count_axe_core_tested_nodes(axe_core_violations, axe_core_incomplete, axe_core_passes):
    """
    Calculates the amount of issues which have been tested by Axe-Core
    """
    amount_nodes_checked = 0

    for issues_per_category in [axe_core_violations, axe_core_incomplete, axe_core_passes]:
        for issue in issues_per_category:
            nodes = issue.get("nodes")
            assert len(nodes) > 0

            amount_nodes_checked += len(nodes)

    return amount_nodes_checked



def process_lighthouse_issues(issues, wcag_issues_dict):
    """
    Lighthouse only shows the url
    """
    if issues is None or len(issues) == 0:
        return
    
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

                # assert issue_data.get("details") is not None

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




def integrate_accessibility_tools_results(pa11y, axe_core, lighthouse):
    """
        Integrates the results from different accessibility tools into a unified format.
    """

    '''
        issues_automatic : contains all automatic found issues which do not require human checking
        issues_manual : contains all issues which have to be checked manually again
    '''
    issues_automatic = {}
    issues_manual = {}

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
    process_axe_core_issues(axe_core_violations, issues_automatic)
    process_axe_core_issues(axe_core_incomplete, issues_manual)

    # get the amount of nodes which have been checked by axe-core
    total_nodes_checked = count_axe_core_tested_nodes(axe_core_violations, axe_core_incomplete, axe_core_passes)

    '''
        2. Pa11y only shows errors/violations
    '''
    process_pa11y_issues(pa11y, issues_automatic)

    '''
        3. Lighthouse returns multiple informations
        audits : all WCAG-rules similar to axe-core, however no information about the amount of nodes tested
        categories : Information about categories tested (in this case only "accessibility"). Interesting: Lighthouse releases final score. Can be used as another benchmark
    '''
    if lighthouse is None:
        lighthouse_audits = None
        lighthouse_accessibility_score = None
    else:
        lighthouse_audits = lighthouse["audits"]
        lighthouse_accessibility_score = lighthouse["categories"].get("accessibility").get("score")
        
    process_lighthouse_issues(lighthouse_audits, issues_automatic)

    issues_automatic = calculate_max_issue_counts(issues_automatic)
    issues_automatic_json, total_nodes_failed = create_accessibility_report(issues_automatic)

    issues_overview_json = create_overview_report(lighthouse_accessibility_score, total_nodes_checked, total_nodes_failed)

    return issues_automatic_json, issues_overview_json
    

