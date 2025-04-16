import os
import json
import matplotlib.pyplot as plt

'''
    Analysis of .json files which contain the accessibility issues of html files
'''

CURR_DIR = os.path.dirname(os.path.realpath(__file__))
INPUT_JSON_DIR = os.path.join(CURR_DIR, '..', 'Input', 'json', 'manual')

ISSUES_DICT = {}

'''
    This function returns a map describing which accessibility issue has been found by which source.

    Therefore, we are looking into the details of each accessibility issue reported. The source (axe-core, lighthouse, pa11y)
    which has reported the most amount of details will get the amount.
    Only exception: If there is an entry with Manual-Inspection, then Manual-Inspection will get the amount.
'''

# Issues are going to be listed
def list_and_add_issues(data, sources_dict):
    global ISSUES_DICT

    amount_total = 0

    for accessibility_issue in data:
        wcag_id = accessibility_issue.get('wcag_id')
        url = accessibility_issue.get('axe_url')
        impact = accessibility_issue.get('impact')
        amount = accessibility_issue.get('amount')
        name = accessibility_issue.get('name')
        issues = accessibility_issue.get('issues')

        amount_total += amount

        if name not in ISSUES_DICT:
            ISSUES_DICT[name] = {
                "impact": impact,
                "total_amount": 0,
                "sources": {
                    "Manual-Inspection": {"count_of_max": 0, "count_of_all": 0, "ids_of_max": [], "ids_of_all": []},
                    "axe-core": {"count_of_max": 0, "count_of_all": 0, "ids_of_max": [], "ids_of_all": []},
                    "pa11y": {"count_of_max": 0, "count_of_all": 0, "ids_of_max": [], "ids_of_all": []},
                    "lighthouse": {"count_of_max": 0, "count_of_all": 0, "ids_of_max": [], "ids_of_all": []}
                }
            }

        ISSUES_DICT[name]["total_amount"] += amount

        axe_core = {
            "amount": 0,
            "issues": []
        }
        pa11y = {
            "amount": 0,
            "issues": []
        }
        lighthouse = {
            "amount": 0,
            "issues": []
        }
        found = False


        for issue in issues:
            source = issue.get("source")
            issue_id = issue.get("id")
            issue_description = issue.get("description")

            if source in ISSUES_DICT[name]["sources"]:
                if source == "Manual-Inspection":
                    ISSUES_DICT[name]["sources"][source]["count_of_all"] += amount
                    ISSUES_DICT[name]["sources"][source]["count_of_max"] += amount

                    sources_dict["Manual-Inspection"]["max"] += amount
                    sources_dict["Manual-Inspection"]["absolute"] += amount

                    found = True

                    for i in range(amount):
                        ISSUES_DICT[name]["sources"][source]["ids_of_max"].append(issue_description)
                        ISSUES_DICT[name]["sources"][source]["ids_of_all"].append(issue_description)

                    continue

                ISSUES_DICT[name]["sources"][source]["count_of_all"] += 1
                ISSUES_DICT[name]["sources"][source]["ids_of_all"].append(issue_id)

                if not found:
                    if source == "axe-core":
                        axe_core["amount"] += 1
                        axe_core["issues"].append(issue_id)
                    elif source == "pa11y":
                        pa11y["amount"] += 1
                        pa11y["issues"].append(issue_id)
                    elif source == "lighthouse":
                        lighthouse["amount"] += 1
                        lighthouse["issues"].append(issue_id)
        
        sources_dict["axe-core"]["absolute"] += axe_core["amount"]
        sources_dict["pa11y"]["absolute"] += pa11y["amount"]
        sources_dict["lighthouse"]["absolute"] += lighthouse["amount"]


        if not found:   
            max_amount = max(axe_core["amount"], pa11y["amount"], lighthouse["amount"])

            if axe_core.get("amount") == max_amount:
                ISSUES_DICT[name]["sources"]["axe-core"]["ids_of_max"].append(axe_core.get("issues"))
                ISSUES_DICT[name]["sources"]["axe-core"]["count_of_max"] += max_amount
                sources_dict["axe-core"]["max"] += max_amount

            elif pa11y.get("amount") == max_amount:
                ISSUES_DICT[name]["sources"]["pa11y"]["ids_of_max"].append(pa11y.get("issues"))
                ISSUES_DICT[name]["sources"]["pa11y"]["count_of_max"] += max_amount
                sources_dict["pa11y"]["max"] += max_amount

            elif lighthouse.get("amount") == max_amount:
                ISSUES_DICT[name]["sources"]["lighthouse"]["ids_of_max"].append(lighthouse.get("issues"))
                ISSUES_DICT[name]["sources"]["lighthouse"]["count_of_max"] += max_amount
                sources_dict["lighthouse"]["max"] += max_amount



    return amount_total


# Ranking based on amount sorting
def create_rankings():
    global ISSUES_DICT
    # sort issues_dict by amount
    sorted_issues = sorted(ISSUES_DICT.items(), key=lambda x: x[1]['total_amount'], reverse=True)
    
    return sorted_issues




def json_analyzer(path):
    global ISSUES_DICT

    amount_total = 0
    sources = {
        "Manual-Inspection": {
            "max": 0,
            "absolute": 0
        },
        "pa11y": {
            "max": 0,
            "absolute": 0
        },
        "axe-core": {
            "max": 0,
            "absolute": 0
        },
        "lighthouse": {
            "max": 0,
            "absolute": 0
        }
    }

    for file in os.listdir(path):
        with open(os.path.join(INPUT_JSON_DIR, file)) as f:
            # print("Analyzed: ", file)
            data = json.load(f)
        
        amount = list_and_add_issues(data, sources)
        amount_total += amount

    
    sorted_issues = create_rankings()

    for i in range(len(sorted_issues)):
        key, values = sorted_issues[i]
        print(f"{i+1}. {key} - {values['impact']} - {values['total_amount']}")

        for source in ISSUES_DICT[key]["sources"]:
            ISSUES_DICT[key]["sources"].get(source)["count_of_max"]
            print(f"Source: {source} with: Max = {ISSUES_DICT[key]["sources"].get(source)["count_of_max"]}, Total = {ISSUES_DICT[key]["sources"][source]["count_of_all"]}")
    
    print("Amount final: ", amount_total)
    print("Average per File: ", float(amount_total/53))

    print("stop")
                



json_analyzer(INPUT_JSON_DIR)