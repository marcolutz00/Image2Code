from collections import Counter

def get_html_snippets(html_generated, accessibility_data) -> list:
    """
        Extracts those html snippets from generated html that have accessibility violations.
        returns list of 
    """
    field_for_tool = {
        "axe-core":lambda i: i["nodes"]["html"],
        "pa11y": lambda i: i["original_issue"]["context"],
        "lighthouse":lambda i: i["details"]["node"]["snippet"],
    }

    snippets = []

    for issue_group in accessibility_data:
        # determine which tool found max
        count_all_tools = Counter(x["source"] for x in issue_group["issues"])
        tool_max_count = count_all_tools.most_common(1)[0]

        for issue in issue_group["issues"]:
            # Only tool with max amount relevant
            if issue["source"] != tool_max_count or issue["impact"] == "tbd":
                continue

            try:
                snippet = field_for_tool[tool_max_count](issue).strip()
            except KeyError:
                snippet = "null"
            
            message = issue.get("title") or issue.get("failureSummary") or "n/a"
            id_violation = issue.get("id")

            snippets.append({"snippet": snippet, "id": id_violation, "msg": message})

    return snippets

