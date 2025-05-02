import os
import json
import copy

'''
    Analysis of .json files which contain the accessibility issues of html files
'''

CURR_DIR = os.path.dirname(os.path.realpath(__file__))
INPUT_INSIGHTS_DIR = os.path.join(CURR_DIR, '..', 'Input', 'insights')
INPUT_ACCESSIBILITY_DIR = os.path.join(CURR_DIR, '..', 'Input', 'accessibility', 'manual')

'''
TODO: 
- WO WURDE DURCH MANUAL-INSPECTION MEHR GEFUNDEN? NACH TEST MÜSSTEN ES 6 FILES VOR DEM FEHLER SEIN
- BENCHMARKS BERECHNEN

'''

'''
    This function returns a map describing which accessibility issue has been found by which source.

    Therefore, we are looking into the details of each accessibility issue reported. The source (axe-core, lighthouse, pa11y)
    which has reported the most amount of details will get the amount.
    Only exception: If there is an entry with Manual-Inspection, then Manual-Inspection will get the amount.
'''

# Issues are going to be listed
def analyze_accessibility_issues(global_issues_dict):
    amount_automatic_nodes_failed_all_files = 0
    amount_manual_checks_failed_all_files = 0

    for file in os.listdir(INPUT_ACCESSIBILITY_DIR):
        base_name = file.split(".")[0]
        insight_name = f'overview_{base_name}.json'

        with open(os.path.join(INPUT_INSIGHTS_DIR, insight_name)) as ir:
            insight_data = json.load(ir)
        
        with open(os.path.join(INPUT_ACCESSIBILITY_DIR, file)) as ar:
            accessibility_data = json.load(ar)

        automatic = accessibility_data.get("automatic")
        manual = accessibility_data.get("manual")
        manual_checks_catalog_path = os.path.join(CURR_DIR, 'manualTestCatalog.json')

        automatic_checks_result = analyze_automatic_accessibility_issues(automatic, global_issues_dict["automatic"])
        manual_checks_result = analyze_manual_accessibility_issues(manual, global_issues_dict["manual"], manual_checks_catalog_path)

        amount_automatic_nodes_failed_all_files += automatic_checks_result['amount_nodes_failed']
        amount_manual_checks_failed_all_files += manual_checks_result['amount_checks_failed']

        overwrite_insights(insight_data, automatic_checks_result, manual_checks_result)

        with open(os.path.join(INPUT_INSIGHTS_DIR, insight_name), 'w', encoding='utf-8') as iw:
            json.dump(insight_data, iw)
    
    return amount_automatic_nodes_failed_all_files, amount_manual_checks_failed_all_files


# Analyzes the manual checks
def analyze_manual_accessibility_issues(data, global_issues_dict, catalog_file_path):
    with open(catalog_file_path) as tc:
        test_catalog = json.load(tc)
    
    passed_checks = {}
    failed_checks = {}

    # get manual checks from json files
    if "checks" in data:
        manual_checks = data["checks"]

        for check_id, status in manual_checks.items():
            if check_id in test_catalog:
                check_description = test_catalog[check_id]
                name = check_description["name"]

                result_overview = {
                    "name": name
                }

                # Assign the issues to right array, depending on status
                if status.lower() == "pass":
                    passed_checks[name] = result_overview
                elif status.lower() == "fail":
                    failed_checks[name] = result_overview

                    if name not in global_issues_dict:
                        global_issues_dict[name] = {
                            "id": name,
                            "sources": "Manual-Inspection",
                            "amount_nodes_failed": 1
                        }
                    else:
                        global_issues_dict[name]["amount_nodes_failed"] += 1

                else: 
                    raise(f"Unknown status: {status} for check ID: {check_id}")
    
    output = {
        'amount_checks': len(passed_checks.items()) + len(failed_checks.items()),
        'amount_checks_failed': len(failed_checks.items()),
        'objects_checks_passed': passed_checks,
        'objects_checks_failed': failed_checks
    }
    
    return output


def analyze_automatic_accessibility_issues(data, global_issues_dict):
    # While global_issues_dict serves for all files, local_issues_dict does only serve for one file
    local_issues_dict = {}
    amount_nodes_failed_file = 0

    for accessibility_issue in data:
        wcag_id = accessibility_issue.get('wcag_id')
        url = accessibility_issue.get('url')
        impact = accessibility_issue.get('impact')
        amount = accessibility_issue.get('amount_nodes_failed')
        assert amount != None
        name = accessibility_issue.get('name')
        issues_details = accessibility_issue.get('issues')
        
        issue_object = create_issues_dict_entry(wcag_id, url)
        issue_object["impact"] = impact
        issue_object["amount_nodes_failed"] = amount

        local_issues_dict[name] = issue_object

        if name not in global_issues_dict:
            issue_object_copy = copy.deepcopy(issue_object)
            global_issues_dict[name] = issue_object_copy
        

        amount_nodes_failed_file += amount

        for issues_detail in issues_details:
            source = issues_detail.get("source")
            issue_id = issues_detail.get("id")
            issue_description = issues_detail.get("description")

            if source in local_issues_dict[name]["sources"]:
                if source == "Manual-Inspection":
                    local_issues_dict[name]["sources"][source]["amount"] += amount
                    global_issues_dict[name]["sources"][source]["amount"] += amount

                    for i in range(amount):
                        local_issues_dict[name]["sources"][source]["ids"].append(issue_description)
                        global_issues_dict[name]["sources"][source]["ids"].append(issue_description)

                    continue

                local_issues_dict[name]["sources"][source]["amount"] += 1
                local_issues_dict[name]["sources"][source]["ids"].append(issue_id)
                global_issues_dict[name]["sources"][source]["amount"] += 1
                global_issues_dict[name]["sources"][source]["ids"].append(issue_id)

    output = {
        'amount_nodes_failed': amount_nodes_failed_file,
        'issues_details': local_issues_dict
    }

    return output


def overwrite_insights(insight_data, automatic_data, manual_data):
    if insight_data["automatic_checks"]["total_nodes_failed"] != automatic_data["amount_nodes_failed"]:
        print("Change of total_nodes_failed, probably due to manual inspection")
        insight_data["automatic_checks"]["total_nodes_failed"] = automatic_data["amount_nodes_failed"]
    
    insight_data["manual_checks"]["total_checks"] = manual_data["amount_checks"]
    insight_data["manual_checks"]["failed_checks"] = manual_data["amount_checks_failed"]

    automatic_issues_details = automatic_data["issues_details"]

    insight_data["details_checks"] = {}
    for name, issue in automatic_issues_details.items():
        insight_data["details_checks"][name] = issue

    for name, issue in manual_data["objects_checks_failed"].items():
        insight_data["details_checks"][name] = issue
        
    


def create_issues_dict_entry(id, url):
    return {
        "id": id,
        "url": url,
        "impact": "tbd",
        "amount_nodes_failed": 0,
        "sources": {
            "Manual-Inspection": {"amount": 0, "ids": []},
            "axe-core": {"amount": 0, "ids": []},
            "pa11y": {"amount": 0, "ids": []},
            "lighthouse": {"amount": 0, "ids": []}
        }
    }



# Ranking based on amount sorting
def sort_issues_by_amount(issues_dict):
    # sort issues_dict by amount
    sorted_issues = sorted(issues_dict.items(), key=lambda x: x[1]['amount_nodes_failed'], reverse=True)
    
    return sorted_issues



# Create dics of how often which precise issue has been found -> no categories but precise issue ID
def count_issue_occurrences(distribution_of_ids, source):
    for id in source["ids"]:
        if id in distribution_of_ids:
            distribution_of_ids[id] += 1
        else:
            distribution_of_ids[id] = 1




def print_result_files(sorted_issues, issues_dict):
    for i in range(len(sorted_issues)):
        key, values = sorted_issues[i]
        print(f"{i+1}. {key} - {values['impact']} - {values['amount_nodes_failed']}")

        distribution_of_ids = {}
        for source in issues_dict[key]["sources"]:
            print(f"Source: {source} with {issues_dict[key]["sources"].get(source)["amount"]} issues found")
            count_issue_occurrences(distribution_of_ids, issues_dict[key]["sources"][source])

        # print ids
        print("IDs: " + ", ".join([f"{key}:{value}" for key, value in distribution_of_ids.items()]) if distribution_of_ids else "Keine IDs gefunden")  

                

def main():
    issues_dict = {
        "automatic": {},
        "manual": {} 
    }

    amount_automatic_nodes_failed_all_files, amount_manual_checks_failed_all_files = analyze_accessibility_issues(issues_dict)
    
    sorted_issues = sort_issues_by_amount(issues_dict)

    print_result_files(sorted_issues, issues_dict)

    print("Amount Issues final: ", amount_automatic_nodes_failed_all_files)
    print("Average Issues per File: ", float(amount_automatic_nodes_failed_all_files/53))


if __name__ == "__main__":
    main()