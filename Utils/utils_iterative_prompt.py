import os
import sys
from bs4 import BeautifulSoup

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import Utils.utils_html as utils_html

def extract_issues_tools(accessibility_data: dict, source_show: bool=False) -> list:
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

    for issue_group in accessibility_data["automatic"]:
        bucket = {}
        for issue in issue_group["issues"]:
            # Only tool with max amount relevant
            if issue_group["impact"] == "tbd":
                continue

            try:
                source = issue.get("source")
            except KeyError:
                snippet = "null"

            if bucket.get(source) is None:
                bucket[source] = []
            bucket[source].append(issue)
        
        if len(bucket) == 0:
            continue
        
        chosen_source, chosen_issues = max(bucket.items(), key = lambda x: len(x[1]))

        for issue in chosen_issues:
            try:
                snippet = field_for_tool[chosen_source](issue).strip()
            except KeyError:
                snippet = "null"
            
            message = issue.get("title") or "n/a"
            id_violation = issue.get("id")

            # check if snippet is empty
            if not snippet or snippet == "null":
                snippet = "No code snippet available for this issue."
            
            if source_show:
                snippets.append({"snippet": snippet, "id": id_violation, "source": source, "message": message, "impact": issue_group["impact"]})
            else:
                snippets.append({"snippet": snippet, "id": id_violation, "message": message, "impact": issue_group["impact"]})

    return snippets

def get_violation_snippets(html_generated, accessibility_data) -> list:
    """ 
        Returns combination of whole generated HTML and the snippets of violations ordered as a json
    """
    snippets_reported_tools = extract_issues_tools(accessibility_data)
    
    result = {
        "html": html_generated,
        "accessibility_violations": snippets_reported_tools
    }

    return result


async def process_refinement_llm(client, prompt):

    """
        Starts the inference with the LLM.
        Returns the generated HTML with fixed issues.
    """
    result_raw, tokens_used = await client.refine_frontend_code(prompt)

    # Print token information
    if tokens_used != None:
        print(tokens_used)

    result_clean = utils_html.clean_html_result(result_raw)

    # html_clean = result_clean.replace("\\n", "")

    return result_clean