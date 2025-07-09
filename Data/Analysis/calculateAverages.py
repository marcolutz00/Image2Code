import os
import json

'''
    For each Test Case (Model, Prompt Strategy) there exist 3 test rounds.
    Each test round consists of 53 images.

    -> Therefore, the final result file for each round has to be averaged 
    over 3 test rounds.
'''

RESULTS_ACCESSIBILITY_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Results", "accessibility")
RESULTS_BENCHMARKS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Results", "benchmarks")


def _sort_issues_by_amount(accessibility_issues: dict, files_processed: int) -> list:
    '''
        Sort the issues by the amount of nodes failed in descending order.
        Apart from that, the division by the number of files processed is done here to get average
    '''

    for issue_name, issue_value in accessibility_issues.items():
        issue_value['amount_nodes_failed'] = round(issue_value['amount_nodes_failed'] / files_processed, 2) if files_processed > 0 else 0

    sorted_issues = sorted(accessibility_issues.items(), key=lambda x: x[1]['amount_nodes_failed'], reverse=True)
    return sorted_issues


def _get_result_files(model: str, prompt_strategy: str, path) -> list:
    """
        Gets the result files for a specific model and prompt strategy
    """
    result_files = [f for f in os.listdir(path) if f.startswith(f"{model}_{prompt_strategy}_analysis")]

    if not result_files:
        raise FileNotFoundError(f"No result files found")

    return result_files


def _get_average_accessibility_results(model: str, prompt_strategy: str) -> dict:
    """
        Gets the accessibility result files from each round and calculates the average
    """

    accessibility_files = _get_result_files(model, prompt_strategy, RESULTS_ACCESSIBILITY_PATH)
    print(accessibility_files)

    accessibility_results = []
    for file in accessibility_files:
        with open(os.path.join(RESULTS_ACCESSIBILITY_PATH, file), 'r', encoding="utf-8") as f:
            accessibility_results.append(json.load(f))

    average_accessibility_results = {}

    dates = []
    result_files_processed = len(accessibility_results)
    dataset_files_processed = 0
    total_automatic_nodes_failed = 0
    average_automatic_nodes_failed_per_file = 0
    accessibility_issues = {}

    for result in accessibility_results:
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


def _get_average_benchmark_results(model: str, prompt_strategy: str) -> dict:
    """
        Gets the benchmark result files from each round and calculates the average
    """

    benchmark_files = _get_result_files(model, prompt_strategy, RESULTS_BENCHMARKS_PATH)
    print(benchmark_files)

    benchmarks_results = []
    for file in benchmark_files:
        with open(os.path.join(RESULTS_BENCHMARKS_PATH, file), 'r', encoding="utf-8") as f:
            benchmarks_results.append(json.load(f))
    
    average_benchmark_results = {}

    dates = []
    result_files_processed = len(benchmarks_results)
    overview_files_processed = 0
    benchmark_files_processed = 0
    total_ir = 0
    total_iwir = 0
    total_status_counts = {}
    total_final_score = 0
    total_final_size_score = 0
    total_final_matched_text_score = 0
    total_final_position_score = 0
    total_final_text_color_score = 0
    total_final_clip_score = 0

    for result in benchmarks_results:

        dates.append(result.get("date"))

        overview_results = result.get("overview")
        if overview_results:
            total_ir += overview_results.get("mean_ir", 0)
            total_iwir += overview_results.get("mean_iwir", 0)

            # TODO: Status counts noch nicht richtig
            total_status_counts.update(overview_results.get("status_counts", {}))

            overview_files_processed += overview_results.get("files_processed", 0)

        benchmarks_results = result.get("benchmarks")
        if benchmarks_results:
            total_final_score += benchmarks_results.get("mean_final_score", 0)
            total_final_size_score += benchmarks_results.get("mean_final_size_score", 0)
            total_final_matched_text_score += benchmarks_results.get("mean_final_matched_text_score", 0)
            total_final_position_score += benchmarks_results.get("mean_final_position_score", 0)
            total_final_text_color_score += benchmarks_results.get("mean_final_text_color_score", 0)
            total_final_clip_score += benchmarks_results.get("mean_final_clip_score", 0)
    
    average_benchmark_results = {
        "model": model,
        "prompt_strategy": prompt_strategy,
        "dates": dates,
        "result_files_processed": result_files_processed,
        "average_final_score": round(total_final_score / result_files_processed, 4) if result_files_processed > 0 else 0,
        "average_final_size_score": round(total_final_size_score / result_files_processed, 4) if result_files_processed > 0 else 0,
        "average_final_matched_text_score": round(total_final_matched_text_score / result_files_processed, 4) if result_files_processed > 0 else 0,
        "average_final_position_score": round(total_final_position_score / result_files_processed, 4) if result_files_processed > 0 else 0,
        "average_final_text_color_score": round(total_final_text_color_score / result_files_processed, 4) if result_files_processed > 0 else 0,
        "average_final_clip_score": round(total_final_clip_score / result_files_processed, 4) if result_files_processed > 0 else 0,
    }
                

    return average_benchmark_results





def get_average_results() -> tuple:
    """
        Gets the result files from each round and calculates the average
    """
    model = "openai" # gemini, openai, llama, qwen
    prompt_strategy = "few-shot" # naive, zero-shot, few-shot, reason, iterative, iterative_refine_1, iterative_refine_2, iterative_refine_3, composite_naive, composite_naive_refine

    accessibility_results = _get_average_accessibility_results(model, prompt_strategy)
    benchmark_results = _get_average_benchmark_results(model, prompt_strategy)

    output_path_accessibility = os.path.join(RESULTS_ACCESSIBILITY_PATH, "average", f"{model}_{prompt_strategy}_average_results.json")
    os.makedirs(os.path.dirname(output_path_accessibility), exist_ok=True)
    output_path_benchmarks = os.path.join(RESULTS_BENCHMARKS_PATH, "average", f"{model}_{prompt_strategy}_average_results.json")
    os.makedirs(os.path.dirname(output_path_benchmarks), exist_ok=True)

    with open(output_path_accessibility, 'w') as f:
        json.dump(accessibility_results, f, indent=2)
    with open(output_path_benchmarks, 'w') as f:
        json.dump(benchmark_results, f, indent=2)

    return accessibility_results, benchmark_results





if __name__ == "__main__":
    print("Start average results...")
    accessibility_results, benchmark_results = get_average_results()