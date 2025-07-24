import os
import json
import copy
import datetime
from pathlib import Path
import sys
import os

PROJECT_ROOT = Path(__file__).absolute().parents[2]
sys.path.append(str(PROJECT_ROOT))
from Benchmarks import accessibilityBenchmarks

CURR_DIR = os.path.dirname(os.path.realpath(__file__))
RESULT_DIR = os.path.join(CURR_DIR, "..", "..", "Results", "accessibility")



'''
    Analysis of .json files which contain the accessibility issues of html files

    Important: this version is without manual inspection
'''



def _analyze_accessibility_issues(global_issues_dict, accessibility_dir, insights_dir):
    '''
        This function returns a map describing which accessibility issue has been found by which source.

        Therefore, we are looking into the details of each accessibility issue reported. The source (axe-core, lighthouse, pa11y)
        which has reported the most amount of details will get the amount.

    '''
    amount_automatic_nodes_failed_all_files = 0
    files_processed = 0

    for file in os.listdir(accessibility_dir):
    # chek if directory
        if file.startswith(".") or not os.path.isfile(os.path.join(accessibility_dir, file)):
            continue

        base_name = file.split(".")[0]

        if base_name.startswith("analysis"):
            continue

        print(f"Processing file: {base_name}")
        files_processed += 1
        insight_name = f'overview_{base_name}.json'


        with open(os.path.join(insights_dir, f"overview_{file}")) as ir:
            insight_data = json.load(ir)
        
        with open(os.path.join(accessibility_dir, file)) as ar:
            accessibility_data = json.load(ar)

        automatic = accessibility_data.get("automatic")

        automatic_checks_result = _analyze_automatic_accessibility_issues(automatic, global_issues_dict["automatic"])

        amount_automatic_nodes_failed_all_files += automatic_checks_result['amount_nodes_failed']

        benchmarks_result = _calculcate_benchmarks(insight_data, automatic_checks_result)

        _change_insights(insight_data, automatic_checks_result, benchmarks_result)

        _write_json_result(insight_data, os.path.join(insights_dir, insight_name))
    
    return amount_automatic_nodes_failed_all_files, files_processed


# Classify the accessibility issues into categories
def _classify_accessibility_issues(checks_result, name):
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
            print(f"Unknown impact: {issue['impact']} for issue: {issue}")
        
    return amount_nodes_critical, amount_nodes_serious, amount_nodes_moderate, amount_nodes_minor

# Calculates the benchmarks for the accessibility issues
def _calculcate_benchmarks(insight_data, automatic_checks_result):
    obj_accessibility_benchmarks = accessibilityBenchmarks.AccessibilityBenchmarks()

    # 1. Benchmark for Automatic checks
    amount_nodes_failed = automatic_checks_result['amount_nodes_failed']
    amount_nodes_checked = insight_data["automatic_checks"]["total_nodes_checked"]
    amount_nodes_critical, amount_nodes_serious, amount_nodes_moderate, amount_nodes_minor = _classify_accessibility_issues(automatic_checks_result, "issues_details")

    # Inaccessibility rate
    automatic_inaccessibility_rate = obj_accessibility_benchmarks.calculate_inaccessibility_rate(amount_nodes_failed, amount_nodes_checked)
    # Impact-weighted inaccessibility rate
    automatic_impact_weighted_inaccessibility_rate = obj_accessibility_benchmarks.calculate_impact_weighted_inaccessibility_rate(amount_nodes_critical, amount_nodes_serious, amount_nodes_moderate, amount_nodes_minor)

    # 2. Get status
    automatic_status = obj_accessibility_benchmarks.calculate_status(automatic_inaccessibility_rate, automatic_impact_weighted_inaccessibility_rate)

    return {
        "automatic_checks": {
            "inaccessibility_rate": automatic_inaccessibility_rate,
            "impact_weighted_inaccessibility_rate": automatic_impact_weighted_inaccessibility_rate,
            "status": automatic_status
        }
    }



def _analyze_automatic_accessibility_issues(data, global_issues_dict):
    '''
        Create dictionary for each accessibility issue (automatic tests)
        While global_issues_dict serves for all files, local_issues_dict does only serve for one file
    '''

    local_issues_dict = {}
    amount_nodes_failed_file = 0

    for accessibility_issue in data:
        wcag_id = accessibility_issue.get('wcag_id')
        url = accessibility_issue.get('url')
        impact = accessibility_issue.get('impact')

        '''
            There are very many accessibility issues out there which I can not cover all.
            Therefore, I will only cover the most important ones which are defined in the mapping

            -> This means, I will skip not defined issues here
        '''
        if impact == "tbd":
            continue

        amount = accessibility_issue.get('amount_nodes_failed')
        assert amount != None
        name = accessibility_issue.get('name')
        issues_details = accessibility_issue.get('issues')
        
        issue_object = _create_issues_dict_entry()
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

    _get_relative_issues(global_issues_dict, local_issues_dict)

    output = {
        'amount_nodes_failed': amount_nodes_failed_file,
        'issues_details': local_issues_dict
    }

    return output

# Get the relative issues: Relative issues are those which have found the biggest amount of an issue in a file
# relative = max(amount of issues found by axe-core, pa11y, lighthouse)
def _get_relative_issues(global_issues_dict, local_issues_dict):
    for name, issue in local_issues_dict.items():
        found = False
        for source, source_data in issue["sources"].items():
            # now compare if manual, axe-core, pa11y or lighthouse is bigger
            if source_data["amount"] == issue["amount_nodes_failed"] and not found:
                found = True
                current_amount = global_issues_dict[name]["sources"][source].get("amount_relative", 0)
                global_issues_dict[name]["sources"][source]["amount_relative"] = current_amount + source_data["amount"]
                

# Overwrite the overview_[file_name].json file with the new data
def _change_insights(insight_data, automatic_data, benchmarks_result):
    if insight_data["automatic_checks"]["total_nodes_failed"] != automatic_data["amount_nodes_failed"]:
        print("Change of total_nodes_failed, probably due to manual inspection")
        insight_data["automatic_checks"]["total_nodes_failed"] = automatic_data["amount_nodes_failed"]

    automatic_data_copy = copy.deepcopy(automatic_data)

    automatic_issues_details = automatic_data_copy["issues_details"]

    insight_data["details_checks"] = {}
    for name, issue in automatic_issues_details.items():
        # store distinct values for each source
        for source in issue["sources"]:
            issue["sources"][source]["ids"] = list(set(issue["sources"][source]["ids"]))
        insight_data["details_checks"][name] = issue

    
    # Define benchmarks
    insight_data["benchmark"] = {
        "automatic_ir": benchmarks_result["automatic_checks"]["inaccessibility_rate"],
        "automatic_iw-ir": benchmarks_result["automatic_checks"]["impact_weighted_inaccessibility_rate"]
    }

    # Define status
    insight_data["overall_status"] = {
        "automatic": benchmarks_result["automatic_checks"]["status"],
    }

        
    
# Creates default dictionary for each accessibility issue
def _create_issues_dict_entry():
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
def _sort_issues_by_amount(issues_dict):
    # sort issues_dict by amount
    sorted_issues = sorted(issues_dict.items(), key=lambda x: x[1]['amount_nodes_failed'], reverse=True)
    
    return sorted_issues



# Merge dicts
def _build_ranking(sorted_issues, issues_dict, automatic):
    issues_json = []
    if automatic:
        distribution_of_sources = {
            "absolute": {},
            "relative": {}
        }
    else:
        distribution_of_sources = {}

    for rank, (name, values) in enumerate(sorted_issues, start=1):
        distribution_of_ids = {}
        if automatic:
            for source, source_values in issues_dict[name]["sources"].items():
                distribution_of_sources["absolute"][source] = distribution_of_sources["absolute"].get(source, 0) + source_values["amount"]
                distribution_of_sources["relative"][source] = distribution_of_sources["relative"].get(source, 0) + source_values["amount_relative"]
                for id in source_values["ids"]:
                    distribution_of_ids[id] = distribution_of_ids.get(id, 0) + 1
        else:
            id = values["id"]
            source = values["sources"]
            for i in range(values["amount_nodes_failed"]):
                distribution_of_sources[source] = distribution_of_sources.get(source, 0) + 1
                distribution_of_ids[id] = distribution_of_ids.get(id, 0) + 1

        issues_json.append({
            "rank": rank,
            "name": name,
            "impact": values["impact"],
            "amount_nodes_failed": values["amount_nodes_failed"],
            "sources": values["sources"],
            "ids_distribution": distribution_of_ids
        })

    return issues_json, distribution_of_sources



# Create json output 
def _build_json_output(sorted_issues_automatic, issues_dict_automatic, total_auto_nodes, files_processed, date):
    issues_json_automatic, distribution_source_automatic = _build_ranking(sorted_issues_automatic, issues_dict_automatic, True)

    summary_json = {
        "timestamp": date,
        "files_processed": files_processed,
        "total_automatic_nodes_failed": total_auto_nodes,
        "average_automatic_nodes_failed_per_file": round(total_auto_nodes / files_processed, 2) if files_processed else 0,
    }

    return {"summary": summary_json, 
            "issues_automatic": issues_json_automatic, 
            "distribution_sources_automatic": distribution_source_automatic, 
            }

# Write json result to file
def _write_json_result(content, out_path):
    out_path = Path(out_path)
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(content, fh, ensure_ascii=False, indent=2)


def overwrite_insights(accessibility_dir, insights_dir, model, prompt_strategy, date):
    '''
        Overwrites the insights
    '''
    issues_dict = {
        "automatic": {},
    }

    amount_automatic_nodes_failed_all_files, files_processed = _analyze_accessibility_issues(issues_dict, accessibility_dir, insights_dir)
    
    sorted_issues_automatic = _sort_issues_by_amount(issues_dict["automatic"])

    json_output_final = _build_json_output(
        sorted_issues_automatic,
        issues_dict["automatic"],
        amount_automatic_nodes_failed_all_files,
        files_processed,
        date
    )

    if model and prompt_strategy and date:
        out_path = os.path.join(RESULT_DIR, f'{model}_{prompt_strategy}_analysis_accessibility_{date}.json')
    else:
        out_path = os.path.join(RESULT_DIR, f'input_analysis_accessibility.json')
    print(f"Writing insights to {out_path}")
    _write_json_result(json_output_final, out_path)



def calculate_insights(accessibility_dir, insight_dir, model, prompt_strategy, date):
    '''
       Calculates Insights:
       Accessibility Violation Ranking and benchmarks are calculated
       Place for the final insight overview: Results/[model]_[prompt-technique]_analysisAccessibilityIssues.json
    '''
    if "iterative" in prompt_strategy or "composite" in prompt_strategy or "agent" in prompt_strategy:
        base_name_strat = prompt_strategy.split("_")[0]
        # Find amount of dirs that start with iterative
        insight_dirs_strats = [d for d in os.listdir(insight_dir) if d.startswith(base_name_strat)]
        if not insight_dirs_strats:
            print("No iterative directories found.")
        else:
            for prompt_strat in insight_dirs_strats:
                insight_dir_path = os.path.join(insight_dir, prompt_strat, date)
                accessibility_dir_path = os.path.join(accessibility_dir, prompt_strat, date)
                overwrite_insights(accessibility_dir_path, insight_dir_path, model, prompt_strat, date)

    else:
        accessibility_prompt_dir = os.path.join(accessibility_dir, prompt_strategy, date)
        insight_prompt_dir = os.path.join(insight_dir, prompt_strategy, date)
        overwrite_insights(accessibility_prompt_dir, insight_prompt_dir, model, prompt_strategy, date)

        

# if __name__ == "__main__":
#     overwrite_insights()