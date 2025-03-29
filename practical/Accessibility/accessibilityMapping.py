import re

'''
    This function is used to map the issues found by different accessibility testing tools
    to one common format.
    Since the tools use either the wcag id (e.g. wcag2a 1.1.1) or the link to the wcag page
    (e.g. https://dequeuniversity.com/rules/axe/4.10/aria-meter-name), we need to map them 
    based on both the id and the link.
'''


wcag_issues_dict = { }

# Pa11y only shows the wcag id, but not the link
def pa11y_mapping(issues):
    for issue in issues:
        issue_id = issue["code"].split(".")[3]
        issue_id = "wcag" + str(issue_id).replace("_", "")


        found = False
        for (existing_wcag_id, existing_url), issues_list in wcag_issues_dict.items():
            if issue_id == existing_wcag_id:
                issues_list.append(issue)
                found = True
                break
        
        # if no match found, create new entry
        if not found:
            wcag_issues_dict[(issue_id, None)] = [issue]


# Axe-core shows the link and wcag id
def axe_core_mapping(issues):
    for issue in issues:
        issue_link = issue["helpUrl"].split("?")[0]

        # Find right tag (z.B. wcag311, wcag421)
        issue_id = None
        for tag in issue["tags"]:
            if tag.startswith("wcag") and tag not in ["wcag2a", "wcag2aa", "wcag2aaa"]:
                issue_id = tag
                break
        
        found = False
        for (existing_wcag_id, existing_url), issues_list in wcag_issues_dict.items():
            if issue_id == existing_wcag_id or issue_link == existing_url:
                issues_list.append(issue)
                found = True
                break

        # if no match found, create new entry
        if not found:
            wcag_issues_dict[(issue_id, issue_link)] = [issue]


# Lighthouse only shows the link
def lighthouse_mapping(issues):
    for issue in issues:
        # Skip if scoreDisplayMode is null since lighthouse shows all
        if issue["scoreDisplayMode"] == "null":
            continue

        description = issue["description"]

        # use regex to find link in description
        link_pattern = re.compile(r'\[.*?\]\((https?://[^\s\)]+)\)')
        link_match = link_pattern.search(description)

        if link_match:
            issue_link = link_match.group(1)
            issue_link = issue_link.split("?")[0]

            found = False
            for (existing_wcag_id, existing_url), issues_list in wcag_issues_dict.items():
                if issue_link == existing_url:
                    issues_list.append(issue)
                    found = True
                    break
            
            # if no match found, create new entry
            if not found:
                wcag_issues_dict[(None, issue_link)] = [issue]
        
        # Use other entry if no link found
        else:
            wcag_issues_dict[("Other", "Other")] = [issue]

            

# Main function to call all mappings
def full_matching(pa11y, axe_core, lighthouse):
    pa11y_mapping(pa11y)
    axe_core_mapping(axe_core)
    lighthouse_mapping(lighthouse)

    return wcag_issues_dict
    

