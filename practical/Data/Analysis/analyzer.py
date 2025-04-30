import os
import json
import matplotlib.pyplot as plt

'''
    Analysis of .json files which contain the accessibility issues of html files
'''

CURR_DIR = os.path.dirname(os.path.realpath(__file__))
INPUT_JSON_DIR = os.path.join(CURR_DIR, '..', 'Input', 'json', 'manual')

'''
    This function returns a map describing which accessibility issue has been found by which source.

    Therefore, we are looking into the details of each accessibility issue reported. The source (axe-core, lighthouse, pa11y)
    which has reported the most amount of details will get the amount.
    Only exception: If there is an entry with Manual-Inspection, then Manual-Inspection will get the amount.
'''
# Issues are going to be listed
def list_and_add_issues(data, sources_dict, issues_dict):
    automatic = data.get("automatic")
    automatic_lighthouse_accessibility_score = automatic.get("lighthouse_accessibility_score")
    automatic_total_nodes_checked = automatic.get("total_nodes_checked")
    automatic_total_nodes_failed = automatic.get("total_nodes_failed")

    manual = data.get("manual")
    manual_checks = manual.get("checks")


    for accessibility_issue in data.get("automatic_issues"):
        wcag_id = accessibility_issue.get('wcag_id')
        url = accessibility_issue.get('axe_url')
        impact = accessibility_issue.get('impact')
        amount_nodes_failed = accessibility_issue.get('amount_nodes_failed')
        name = accessibility_issue.get('name')
        issues = accessibility_issue.get('issues')

        if name not in issues_dict:
            issues_dict[name] = {
                "impact": impact,
                "amount_nodes_failed": 0,
                "sources": {
                    "Manual-Inspection": {"count_of_max": 0, "count_of_all": 0, "ids_of_max": [], "ids_of_all": []},
                    "axe-core": {"count_of_max": 0, "count_of_all": 0, "ids_of_max": [], "ids_of_all": []},
                    "pa11y": {"count_of_max": 0, "count_of_all": 0, "ids_of_max": [], "ids_of_all": []},
                    "lighthouse": {"count_of_max": 0, "count_of_all": 0, "ids_of_max": [], "ids_of_all": []}
                }
            }

        issues_dict[name]["amount_nodes_failed"] += amount_nodes_failed

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

            if source in issues_dict[name]["sources"]:
                if source == "Manual-Inspection":
                    issues_dict[name]["sources"][source]["count_of_all"] += amount_nodes_failed
                    issues_dict[name]["sources"][source]["count_of_max"] += amount_nodes_failed

                    sources_dict["Manual-Inspection"]["max"] += amount_nodes_failed
                    sources_dict["Manual-Inspection"]["absolute"] += amount_nodes_failed

                    found = True

                    for i in range(amount_nodes_failed):
                        issues_dict[name]["sources"][source]["ids_of_max"].append(issue_description)
                        issues_dict[name]["sources"][source]["ids_of_all"].append(issue_description)

                    continue

                issues_dict[name]["sources"][source]["count_of_all"] += 1
                issues_dict[name]["sources"][source]["ids_of_all"].append(issue_id)

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
                issues_dict[name]["sources"]["axe-core"]["ids_of_max"] += axe_core.get("issues")
                issues_dict[name]["sources"]["axe-core"]["count_of_max"] += max_amount
                sources_dict["axe-core"]["max"] += max_amount

            elif pa11y.get("amount") == max_amount:
                issues_dict[name]["sources"]["pa11y"]["ids_of_max"] += pa11y.get("issues")
                issues_dict[name]["sources"]["pa11y"]["count_of_max"] += max_amount
                sources_dict["pa11y"]["max"] += max_amount

            elif lighthouse.get("amount") == max_amount:
                issues_dict[name]["sources"]["lighthouse"]["ids_of_max"] += lighthouse.get("issues")
                issues_dict[name]["sources"]["lighthouse"]["count_of_max"] += max_amount
                sources_dict["lighthouse"]["max"] += max_amount



    return automatic_total_nodes_checked, automatic_total_nodes_failed


# Ranking based on amount sorting
def create_rankings(issues_dict):
    # sort issues_dict by amount
    sorted_issues = sorted(issues_dict.items(), key=lambda x: x[1]['amount_nodes_failed'], reverse=True)
    
    return sorted_issues



# Create dics of how often which precise issue has been found -> no categories but precise issue ID
def create_overview_amount_ids(distribution_of_ids, source):
    for id in source["ids_of_max"]:
        if id in distribution_of_ids:
            distribution_of_ids[id] += 1
        else:
            distribution_of_ids[id] = 1


# Analyzes the manual checks and sets the corresponding values
def manual_issues_analyzer(path):
    for file in os.listdir(path):
        with open(os.path.join(INPUT_JSON_DIR, file), 'rw') as f:
            data = json.load(f)


def json_analyzer(path):
    issues_dict = {}
    amount_nodes_checked_all_files = 0
    amount_nodes_failed_all_files = 0

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
        
        amount_nodes_checked_file, amount_nodes_failed_file = list_and_add_issues(data, sources, issues_dict)
        amount_nodes_checked_all_files += amount_nodes_checked_file
        amount_nodes_failed_all_files += amount_nodes_failed_file

    
    sorted_issues = create_rankings(issues_dict)

    for i in range(len(sorted_issues)):
        key, values = sorted_issues[i]
        print(f"{i+1}. {key} - {values['impact']} - {values['amount_nodes_failed']}")

        distribution_of_ids = {}
        for source in issues_dict[key]["sources"]:
            print(f"Source: {source} with: Max = {issues_dict[key]["sources"].get(source)["count_of_max"]}, Total = {issues_dict[key]["sources"][source]["count_of_all"]}")
            create_overview_amount_ids(distribution_of_ids, issues_dict[key]["sources"][source])

        # print ids
        print("IDs: " + ", ".join([f"{key}:{value}" for key, value in distribution_of_ids.items()]) if distribution_of_ids else "Keine IDs gefunden")  

    print("Amount Checks final: ", amount_nodes_checked_all_files)
    print("Amount Issues final: ", amount_nodes_failed_all_files)
    print("Average Issues per File: ", float(amount_nodes_failed_all_files/53))

    print("stop")
                

def main():
    json_analyzer(INPUT_JSON_DIR)

if __name__ == "__main__":
    main()