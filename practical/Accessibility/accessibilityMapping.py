import re

'''
    This function is used to map the issues found by different accessibility testing tools
    to one common format.
    Since the tools use either the wcag id (e.g. wcag2a 1.1.1) or the url to the wcag page
    (e.g. https://dequeuniversity.com/rules/axe/4.10/aria-meter-name), we need to map them 
    based on both the id and the url.
'''



# Pa11y only shows the wcag id, but not the url
def pa11y_mapping(issues, wcag_issues_dict):
    for issue in issues:
        issue_id = issue["code"].split(".")[3]
        issue_id = "wcag" + str(issue_id).replace("_", "")

        full_issue = {
            "id": issue.get("code", ""),
            "source": "pa11y",
            "title": issue.get("message", ""),
            "description": issue.get("context", ""),
            "impact": issue.get("type", ""),
            "original_issue": issue
        }


        found = False
        for (existing_wcag_id, existing_url), issues_list in wcag_issues_dict.items():
            if issue_id == existing_wcag_id:
                issues_list.append(full_issue)
                found = True
                break
        
        # if no match found, create new entry
        if not found:
            wcag_issues_dict[(issue_id, None)] = [full_issue]


# Axe-core shows the url and wcag id
def axe_core_mapping(issues, wcag_issues_dict):
    for issue in issues:
        issue_url = issue["helpUrl"].split("?")[0]

        # Find right tag (z.B. wcag311, wcag421)
        issue_id = None
        for tag in issue["tags"]:
            if tag.startswith("wcag") and tag not in ["wcag2a", "wcag2aa", "wcag2aaa"]:
                issue_id = tag
                break
        
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
            existing_wcag_id, existing_url = key
            if (issue_id is not None and issue_id == existing_wcag_id) or (issue_url == existing_url):
                issues_list.append(full_issue)
                found = True

                matching_key = None
                if issue_id == existing_wcag_id and existing_url is None and issue_url is not None:
                    matching_key = key

                break
        
        # Update key with url if it was None
        if found and matching_key is not None:
            old_wcag_id, _ = matching_key
            issues_list = wcag_issues_dict.pop(matching_key)  
            wcag_issues_dict[(old_wcag_id, issue_url)] = issues_list

        # if no match found, create new entry
        if not found:
            wcag_issues_dict[(issue_id, issue_url)] = [full_issue]


# Lighthouse only shows the url
def lighthouse_mapping(issues, wcag_issues_dict):
    for issue_id, issue_data in issues.items():
        # Skip if scoreDisplayMode is null since lighthouse shows all
        if issue_data.get("scoreDisplayMode") in ["notApplicable", "manual"]:
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

            found = False
            for (existing_wcag_id, existing_url), issues_list in wcag_issues_dict.items():
                if issue_url == existing_url:
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
                wcag_issues_dict[(None, issue_url)] = [{
                    "id": issue_id,
                    "source": "lighthouse",
                    "title": issue_data.get("title", ""),
                    "description": description,
                    "score": issue_data.get("score"),
                    "details": issue_data.get("details", {})
                }]
        
        # Use other entry if no url found
        else:
            if ("Other", "Other") in wcag_issues_dict:
                wcag_issues_dict[("Other", "Other")].append({
                    "id": issue_id,
                    "source": "lighthouse",
                    "title": issue_data.get("title", ""),
                    "description": description,
                    "score": issue_data.get("score"),
                    "details": issue_data.get("details", {})
                })
            else:
                wcag_issues_dict[("Other", "Other")] = [{
                    "id": issue_id,
                    "source": "lighthouse",
                    "title": issue_data.get("title", ""),
                    "description": description,
                    "score": issue_data.get("score"),
                    "details": issue_data.get("details", {})
                }]


# Convert it to json readable format
def prepare_wcag_issues_json(wcag_issues_dict):
    output = []

    for (wcag_id, url), issues_list in wcag_issues_dict.items():
        item = {
            "wcag_id": wcag_id,
            "url": url,
            "issues": issues_list
        }
        output.append(item)

    return output



# Main function to call all mappings
def full_matching(pa11y, axe_core, lighthouse):
    wcag_issues_dict = {}

    pa11y_mapping(pa11y, wcag_issues_dict)
    axe_core_mapping(axe_core, wcag_issues_dict)
    lighthouse_mapping(lighthouse, wcag_issues_dict)

    wcag_issues_dict = prepare_wcag_issues_json(wcag_issues_dict)

    return wcag_issues_dict
    

