import os
import json

'''
    For each Test Case (Model, Prompt Strategy) there exist 3 test rounds.
    Each test round consists of 53 images.

    -> Therefore, the final result file for each round has to be averaged 
    over 3 test rounds.
'''

RESULTS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Results", "accessibility")


def _sort_issues_by_amount(accessibility_issues, files_processed):
    '''
        Sort the issues by the amount of nodes failed in descending order.
        Apart from that, the division by the number of files processed is done here to get average
    '''

    for issue_name, issue_value in accessibility_issues.items():
        issue_value['amount_nodes_failed'] = round(issue_value['amount_nodes_failed'] / files_processed, 2) if files_processed > 0 else 0

    sorted_issues = sorted(accessibility_issues.items(), key=lambda x: x[1]['amount_nodes_failed'], reverse=True)
    return sorted_issues


def _get_average_accessibility_results(accessibility_results, model, prompt_strategy):
    """
        Gets the accessibility result files from each round and calculates the average
    """
    average_accessibility_results = {}

    dates = []
    result_files_processed = 0
    dataset_files_processed = 0
    total_automatic_nodes_failed = 0
    average_automatic_nodes_failed_per_file = 0
    accessibility_issues = {}

    for result in accessibility_results:
        result_files_processed += 1

        summary_result = result.get("summary")
        if summary_result:
            dates.append(summary_result.get("timestamp"))
            dataset_files_processed += summary_result.get("files_processed", 0)
            total_automatic_nodes_failed += summary_result.get("total_automatic_nodes_failed", 0)
            average_automatic_nodes_failed_per_file += summary_result.get("average_automatic_nodes_failed_per_file", 0)

        automatic_issues_result = result.get("issues_automatic")
        if automatic_issues_result:
            for issue in automatic_issues_result:
                issue_name = issue.get("name")
                issue_impact = issue.get("impact")
                issue_amount_nodes_failed = issue.get("amount_nodes_failed", 0)

                if issue_name not in accessibility_issues:
                    accessibility_issues[issue_name] = {
                        "impact": issue_impact,
                        "amount_nodes_failed": issue_amount_nodes_failed
                    }
                
                else:
                    accessibility_issues[issue_name]["amount_nodes_failed"] += issue_amount_nodes_failed

    # if not prompt_strategy.startswith("iterative_refine"):
    #     assert(dataset_files_processed == result_files_processed * 53)

    # Sort by amount of nodes failed
    accessibility_issues = _sort_issues_by_amount(accessibility_issues, result_files_processed)
    
    average_accessibility_results = {
        "model": model,
        "prompt_strategy": prompt_strategy,
        "dates": dates,
        "result_files_processed": result_files_processed,
        "dataset_files_processed": dataset_files_processed,
        "total_automatic_nodes_failed": round(total_automatic_nodes_failed / result_files_processed, 2) if result_files_processed > 0 else 0,
        "average_automatic_nodes_failed_per_file": round(average_automatic_nodes_failed_per_file / result_files_processed, 2) if result_files_processed > 0 else 0,
        "accessibility_issues": accessibility_issues
    }
                

    return average_accessibility_results


def get_average_results():
    """
        Gets the result files from each round and calculates the average
    """
    model = "gemini" # gemini, openai, llama, qwen
    prompt_strategy = "iterative_refine_3" # naive, zero-shot, reason, iterative, iterative_refine_1, iterative_refine_2, iterative_refine_3

    accessibility_files = [f for f in os.listdir(RESULTS_PATH) if f.startswith(f"{model}_{prompt_strategy}_analysis")]

    print(accessibility_files)
    
    accessibility_results = []
    for file in accessibility_files:
        file_path = os.path.join(RESULTS_PATH, file)
        if os.path.isfile(file_path):
            with open(file_path, 'r') as f:
                file_data = json.load(f)
                accessibility_results.append(file_data) 

    average_results = {}
    average_results["accessibility"] = _get_average_accessibility_results(accessibility_results, model, prompt_strategy)

    output_path = os.path.join(RESULTS_PATH, "average", f"dl_{model}_{prompt_strategy}_average_results.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(average_results, f, indent=2)

    return average_results

if __name__ == "__main__":
    print("Start average results...")
    average_results = get_average_results()