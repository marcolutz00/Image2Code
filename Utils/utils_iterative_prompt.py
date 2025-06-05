

def _extract_issues_tools(accessibility_data) -> list:
    """
        Returns the html snippets which have been stored by the tools 
        Important: This is not yet the lines of code, but only a citation of the tools to make sure which line is affected.
    """
    
    field_for_tool = {
        "axe-core":lambda i: i["nodes"]["html"],
        "pa11y": lambda i: i["original_issue"]["context"],
        "lighthouse":lambda i: i["details"]["node"]["snippet"],
    }

    snippets = []

    for issue_group in accessibility_data:
        for issue in issue_group["issues"]:
            # Only tool with max amount relevant
            if issue_group["impact"] == "tbd":
                continue

            try:
                source = issue.get("source")
                snippet = field_for_tool[tool_max_count](issue).strip()
            except KeyError:
                snippet = "null"
            
            message = issue.get("title") or issue.get("failureSummary") or "n/a"
            id_violation = issue.get("id")

            snippets.append({"snippet": snippet, "id": id_violation, "msg": message})

    return snippets


def get_violation_snippets(html_generated, accessibility_data) -> list:
    """
        Extracts those html snippets from generated html that have accessibility violations.
        returns list of 
    """
    snippets_reported_tools = _extract_issues_tools(accessibility_data)
    

