import os
import json
import copy
import datetime
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).absolute().parents[2]
sys.path.append(str(PROJECT_ROOT))


from Benchmarks import accessibilityBenchmarks

'''
    Analysis of .json files which contain the accessibility issues of html files
'''

CURR_DIR = os.path.dirname(os.path.realpath(__file__))
INPUT_INSIGHTS_DIR = os.path.join(CURR_DIR, '..', 'Input', 'insights')
INPUT_ACCESSIBILITY_DIR = os.path.join(CURR_DIR, '..', 'Input', 'accessibility', 'manual')


'''
    This function returns a map describing which accessibility issue has been found by which source.

    Therefore, we are looking into the details of each accessibility issue reported. The source (axe-core, lighthouse, pa11y)
    which has reported the most amount of details will get the amount.
    Only exception: If there is an entry with Manual-Inspection, then Manual-Inspection will get the amount.
'''

# Analyzes the accessibility issues of all files
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

        benchmarks_result = calculcate_benchmarks(insight_data, automatic_checks_result, manual_checks_result)

        overwrite_insights(insight_data, automatic_checks_result, manual_checks_result, benchmarks_result)

        write_json_result(insight_data, os.path.join(INPUT_INSIGHTS_DIR, insight_name))
    
    return amount_automatic_nodes_failed_all_files, amount_manual_checks_failed_all_files


# Classify the accessibility issues into categories
def classify_accessibility_issues(checks_result, name):
    amount_nodes_critical = 0
    amount_nodes_serious = 0
    amount_nodes_moderate = 0
    amount_nodes_minor = 0

    # Get the amount of critical, serious, moderate and minor issues
    for issue in checks_result[name].values():
        if issue["impact"] == "critical":
            amount_nodes_critical += issue["amount_nodes_failed"]
        elif issue["impact"] == "serious":
            amount_nodes_serious += issue["amount_nodes_failed"]
        elif issue["impact"] == "moderate":
            amount_nodes_moderate += issue["amount_nodes_failed"]
        elif issue["impact"] == "minor":
            amount_nodes_minor += issue["amount_nodes_failed"]
        else:   
            raise(f"Unknown impact: {issue['impact']} for issue: {issue['name']}")
        
    return amount_nodes_critical, amount_nodes_serious, amount_nodes_moderate, amount_nodes_minor

# Calculates the benchmarks for the accessibility issues
def calculcate_benchmarks(insight_data, automatic_checks_result, manual_checks_result):
    # 1. Benchmark for Automatic checks
    amount_nodes_failed = automatic_checks_result['amount_nodes_failed']
    amount_nodes_checked = insight_data["automatic_checks"]["total_nodes_checked"]
    amount_nodes_critical, amount_nodes_serious, amount_nodes_moderate, amount_nodes_minor = classify_accessibility_issues(automatic_checks_result, "issues_details")

    # Inaccessibility rate
    automatic_inaccessibility_rate = accessibilityBenchmarks.calculate_inaccessibility_rate(amount_nodes_failed, amount_nodes_checked)
    # Impact-weighted inaccessibility rate
    automatic_impact_weighted_inaccessibility_rate = accessibilityBenchmarks.calculate_impact_weighted_inaccessibility_rate(amount_nodes_critical, amount_nodes_serious, amount_nodes_moderate, amount_nodes_minor)

    # 2. Benchmark for Manual checks
    amount_nodes_failed = manual_checks_result['amount_checks_failed']
    amount_nodes_checked = manual_checks_result["amount_checks"]
    amount_nodes_critical, amount_nodes_serious, amount_nodes_moderate, amount_nodes_minor = classify_accessibility_issues(manual_checks_result, "objects_checks_failed")

    # Inaccessibility rate
    manual_inaccessibility_rate = accessibilityBenchmarks.calculate_inaccessibility_rate(amount_nodes_failed, amount_nodes_checked)
    # Impact-weighted inaccessibility rate
    manual_impact_weighted_inaccessibility_rate = accessibilityBenchmarks.calculate_impact_weighted_inaccessibility_rate(amount_nodes_critical, amount_nodes_serious, amount_nodes_moderate, amount_nodes_minor)


    # 3. Get status
    automatic_status = accessibilityBenchmarks.calculate_status(automatic_inaccessibility_rate, automatic_impact_weighted_inaccessibility_rate)
    manual_status = accessibilityBenchmarks.calculate_status(manual_inaccessibility_rate, manual_impact_weighted_inaccessibility_rate)

    return {
        "automatic_checks": {
            "inaccessibility_rate": automatic_inaccessibility_rate,
            "impact_weighted_inaccessibility_rate": automatic_impact_weighted_inaccessibility_rate,
            "status": automatic_status
        },
        "manual_checks": {
            "inaccessibility_rate": manual_inaccessibility_rate,
            "impact_weighted_inaccessibility_rate": manual_impact_weighted_inaccessibility_rate,
            "status": manual_status
        }
    }


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
                check_impact = check_description["impact"]
                name = check_description["name"]
                wcag_name = check_description["wcag_name"]

                result_overview = {
                    "impact": check_impact,
                    "amount_nodes_failed": 1,
                    "sources": {
                        "Manual-Inspection": {
                            "amount": 1,
                            "ids": [wcag_name]
                        }
                    }
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

# Create dictionary for each accessibility issue (automatic tests)
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
        
        issue_object = create_issues_dict_entry()
        issue_object["impact"] = impact
        issue_object["amount_nodes_failed"] = amount

        local_issues_dict[name] = issue_object

        if name not in global_issues_dict:
            issue_object_copy = copy.deepcopy(issue_object)
            global_issues_dict[name] = issue_object_copy
        else:
            global_issues_dict[name]["amount_nodes_failed"] += amount
        

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

    get_relative_issues(global_issues_dict, local_issues_dict)

    output = {
        'amount_nodes_failed': amount_nodes_failed_file,
        'issues_details': local_issues_dict
    }

    return output

# Get the relative issues: Relative issues are those which have found the biggest amount of an issue in a file
# relative = max(amount of issues found by axe-core, pa11y, lighthouse)
def get_relative_issues(global_issues_dict, local_issues_dict):
    for name, issue in local_issues_dict.items():
        found = False
        for source, source_data in issue["sources"].items():
            # now compare if manual, axe-core, pa11y or lighthouse is bigger
            if source_data["amount"] == issue["amount_nodes_failed"] and not found:
                found = True
                current_amount = global_issues_dict[name]["sources"][source].get("amount_relative", 0)
                global_issues_dict[name]["sources"][source]["amount_relative"] = current_amount + source_data["amount"]
                

# Overwrite the overview_[file_name].json file with the new data
def overwrite_insights(insight_data, automatic_data, manual_data, benchmarks_result):
    if insight_data["automatic_checks"]["total_nodes_failed"] != automatic_data["amount_nodes_failed"]:
        print("Change of total_nodes_failed, probably due to manual inspection")
        insight_data["automatic_checks"]["total_nodes_failed"] = automatic_data["amount_nodes_failed"]
    
    insight_data["manual_checks"]["total_checks"] = manual_data["amount_checks"]
    insight_data["manual_checks"]["failed_checks"] = manual_data["amount_checks_failed"]

    automatic_data_copy = copy.deepcopy(automatic_data)

    automatic_issues_details = automatic_data_copy["issues_details"]

    insight_data["details_checks"] = {}
    for name, issue in automatic_issues_details.items():
        # store distinct values for each source
        for source in issue["sources"]:
            issue["sources"][source]["ids"] = list(set(issue["sources"][source]["ids"]))
        insight_data["details_checks"][name] = issue

    for name, issue in manual_data["objects_checks_failed"].items():
        insight_data["details_checks"][name] = issue

    
    # Define benchmarks
    insight_data["benchmark"] = {
        "automatic_ir": benchmarks_result["automatic_checks"]["inaccessibility_rate"],
        "automatic_iw-ir": benchmarks_result["automatic_checks"]["impact_weighted_inaccessibility_rate"],
        "manual_ir": benchmarks_result["manual_checks"]["inaccessibility_rate"],
        "manual_iw-ir": benchmarks_result["manual_checks"]["impact_weighted_inaccessibility_rate"],
    }

    # Define status
    insight_data["overall_status"] = {
        "automatic": benchmarks_result["automatic_checks"]["status"],
        "manual": benchmarks_result["manual_checks"]["status"]
    }

        
    
# Creates default dictionary for each accessibility issue
def create_issues_dict_entry():
    return {
        "impact": "tbd",
        "amount_nodes_failed": 0,
        "sources": {
            "Manual-Inspection": {"amount": 0, "amount_relative": 0, "ids": []},
            "axe-core": {"amount": 0, "amount_relative": 0, "ids": []},
            "pa11y": {"amount": 0, "amount_relative": 0, "ids": []},
            "lighthouse": {"amount": 0, "amount_relative": 0, "ids": []}
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



# Create json output 
def build_json_output(sorted_issues, issues_dict, total_auto_nodes, total_manual_failed, files_processed):
    issues_json = []
    for rank, (name, values) in enumerate(sorted_issues, start=1):
        distribution_of_ids = {}
        for source, source_values in issues_dict[name]["sources"].items():
            for id_ in source_values["ids"]:
                distribution_of_ids[id_] = distribution_of_ids.get(id_, 0) + 1

        issues_json.append({
            "rank": rank,
            "name": name,
            "impact": values["impact"],
            "amount_nodes_failed": values["amount_nodes_failed"],
            "sources": values["sources"],
            "ids_distribution": distribution_of_ids
        })

    summary_json = {
        "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
        "files_processed": files_processed,
        "total_automatic_nodes_failed": total_auto_nodes,
        "total_manual_checks_failed": total_manual_failed,
        "average_nodes_failed_per_file": round(total_auto_nodes / files_processed, 2) if files_processed else 0
    }

    return {"summary": summary_json, "issues": issues_json}

# Write json result to file
def write_json_result(content, out_path):
    out_path = Path(out_path)
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(content, fh, ensure_ascii=False, indent=2)


def main():
    issues_dict = {
        "automatic": {},
        "manual": {} 
    }

    amount_automatic_nodes_failed_all_files, amount_manual_checks_failed_all_files = analyze_accessibility_issues(issues_dict)
    
    sorted_issues = sort_issues_by_amount(issues_dict["automatic"])

    json_output_final = build_json_output(
        sorted_issues,
        issues_dict["automatic"],
        total_auto_nodes=amount_automatic_nodes_failed_all_files,
        total_manual_failed=amount_manual_checks_failed_all_files,
        files_processed=len(os.listdir(INPUT_ACCESSIBILITY_DIR))
    )
    out_path = os.path.join(CURR_DIR, 'AnalysisAccessibilityIssues.json')
    write_json_result(json_output_final, out_path)

if __name__ == "__main__":
    main()