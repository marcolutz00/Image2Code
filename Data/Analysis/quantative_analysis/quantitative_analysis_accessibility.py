import matplotlib.pyplot as plt
import json
import os
import sys
from copy import deepcopy
import numpy as np
from scipy.spatial.distance import cosine
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

import Utils.utils_general as utils_general
import Utils.utils_dataset as utils_dataset

BENCHMARKS_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'Benchmarks')


def get_severity_distribution(average_violations_paths: str) -> dict:
    """
    Creates a map of severities across models and prompt strategies.
    """
    severity_distribution_all = {}

    for model, prompt, path in average_violations_paths: 
        average_violations = utils_general.read_json(path).get("accessibility_issues", [])

        severity_distribution = {
            "critical": 0,
            "serious": 0,
            "moderate": 0,
            "minor": 0,
            "unknown": 0
        }

        for _, values in average_violations:
            severity = values.get("impact", "unknown")
            amt = round(values.get("amount_nodes_failed", 0), 0)
            if severity in severity_distribution:
                severity_distribution[severity] += amt
            else:
                print("Severity not found.")

        severity_distribution_all[f"{model}-{prompt}"] = severity_distribution

    return severity_distribution_all



def _structure_and_sort_violations(violations_lists: list, top_violations: int) -> list:
    """
    
    """
    total_violations = {}
    impacts = {}

    for violations_list in violations_lists:
        for name, details in violations_list:
            if name not in total_violations:
                total_violations[name] = 0

            total_violations[name] += details.get("amount_nodes_failed", 0) or 0
            impacts[name] = details.get("impact")

    # sort by biggest amount
    sorted_issue_names = sorted(total_violations.keys(),
        key=lambda x: total_violations[x], reverse=True
    )[:top_violations]

    for violations_list in violations_lists:
        copy_violations_list = {name: deepcopy(details) for name, details in violations_list}

        # Add missing isseus
        for name in sorted_issue_names:
            if name not in copy_violations_list:
                copy_violations_list[name] = {
                    "impact": impacts[name],
                    "amount_nodes_failed": 0
                }

        # return sorted list
        violations_list = [
            [name, copy_violations_list[name]] for name in sorted_issue_names]

    return sorted_issue_names, violations_lists





def plot_bar_average_violations(comparison: list) -> None:
    """
        bar chart plot based on average violations
    """
    
    violations_lists = []

    for _, _, path in comparison:
        data = utils_general.read_json(path)

        violations_list = data.get("accessibility_issues", [])
        violations_lists.append(violations_list)
    
    # amount of violations in plot
    top_violations = 10
    violation_names, structured_violations_lists = _structure_and_sort_violations(violations_lists, top_violations)

    x_ticks = np.arange(len(violation_names))
    width_per_bar = 0.8 / len(comparison)
    offsets = [i * width_per_bar for i in range(len(comparison))]
    number_of_comparisons = len(comparison)

    plt.figure(figsize=(12, 6))

    # Plot the bar
    for i, violations_list in enumerate(structured_violations_lists):
        violations_dict = {name: values for name, values in violations_list}

        y_values = [
            violations_dict.get(name, {"amount_nodes_failed": 0})["amount_nodes_failed"]
            for name in violation_names
        ]

        bars = plt.bar(
            x_ticks + offsets[i],
            y_values,
            width=width_per_bar,
            label=f"{comparison[i][0]}-{comparison[i][1]}"
        )


        # https://www.geeksforgeeks.org/python/adding-value-labels-on-a-matplotlib-bar-chart/
        for bar in bars:
            height = bar.get_height()
            plt.text(
                x=bar.get_x() + bar.get_width()/2,
                y=height + 0.1,
                s=f"{height:.0f}",
                ha="center", fontsize=8
            )

    plt.xticks(
        x_ticks + (number_of_comparisons-1)*width_per_bar/2,
        violation_names,
        rotation=45,
        ha="right"
    )

    plt.ylabel("Average Nodes failed")
    plt.legend()
    plt.tight_layout()
    plt.show()



def plot_cake_average_violations(accessibility_path: str) -> None:
    """
        cake chart plot based on average violations
        https://stackoverflow.com/questions/71669256/matplotlib-pie-chart-label-customize-with-percentage
    """

    top_violations = 7
    other_added = False

    data = utils_general.read_json(accessibility_path)
    violations_list = data.get("accessibility_issues", [])

    labels = []
    values = []
    for name, details in violations_list:
        if len(labels) >= top_violations:
            if not other_added:
                labels.append("Other")
                values.append(details.get("amount_nodes_failed", 0))
                other_added = True
            else:
                values[-1] += details.get("amount_nodes_failed", 0)

            continue

        labels.append(name)
        values.append(details.get("amount_nodes_failed", 0))

    # print(len(labels), len(values))

    values = np.array(values)

    # fig, ax = plt.subplots(1, 1, figsize=(12, 12))
    fig, ax = plt.subplots(figsize=(9, 9), constrained_layout=True)

    ax.pie(
        values,
        labels=labels,
        autopct="%1.1f%%",
        # pctdistance=0.8
    )
    ax.axis("equal") 

    plt.title("Average Accessibility Violations")
    plt.tight_layout()
    plt.show()


def _build_vector_space(comparison: list):
    """
        Build vector space for heatmap
        Vector Length : len(violations in mapping)
    """

    wcag_mapping_path = os.path.join(BENCHMARKS_PATH, '..', 'Accessibility', 'mappingCsAndAxeCore.json')
    wcag_mapping = utils_general.read_json(wcag_mapping_path)
    rule_names = [mapping.get("name") for mapping in wcag_mapping]
    rule_index_map = {name: index for index, name in enumerate(rule_names)}


    vector_space = {}
    
    # Iterate over all comparisons (e.g. gemini-naive, gemini-zero-shot)
    for model, prompt, path in comparison:
        experiment_id = str(hash(f"{model}{prompt}{path}"))
        # Iterate over each file 
        for file in [f for f in utils_dataset.sorted_alphanumeric(os.listdir(path)) if f.endswith('.json')]:
            file_base = file.split(".")[0]
            # print(file_base)

            if file_base not in vector_space:
                vector_space[file_base] = {}

            file_path = os.path.join(path, file)
            data_file = utils_general.read_json(file_path)

            # build vector 
            vector = np.zeros(len(rule_names))

            # Iterate over all issues file
            for issue in data_file.get("automatic", []):
                rule_name = issue.get("name")
                if rule_name in rule_index_map:
                    index = rule_index_map[rule_name]
                    vector[index] += issue.get("amount_nodes_failed", 0)
        
            # Add vector to vector space
            vector_space[file_base][experiment_id] = vector


    return vector_space, rule_names


def _calculate_cosine_similarity(vector_space: dict):
    """
        Calculate cosine similarity between vectors in vector space
        -> Each column in the heatmap is a comparison between two runs 
    """

    cosine_similarity_dict = {}
    
    for file, vector in vector_space.items():
        # Calculate similarity for each pair (except itself)
        if file not in cosine_similarity_dict:
            cosine_similarity_dict[file] = {}
        
        seen_experiment_runs = set()
        for experiment_id1, vector1 in vector.items():
            for experiment_id2, vector2 in vector.items():
                if experiment_id1 != experiment_id2 and (experiment_id2, experiment_id1) not in seen_experiment_runs:
                    seen_experiment_runs.add((experiment_id1, experiment_id2))
                    
                    # if no violations then 0-vector
                    if np.all(vector1 == 0) and np.all(vector2 == 0):
                        cosine_similarity_dict[file][f"{experiment_id1}_vs_{experiment_id2}"] = 1.0
                        continue
                    similarity = 1 - cosine(vector1, vector2)
                    cosine_similarity_dict[file][f"{experiment_id1}_vs_{experiment_id2}"] = similarity

    
    return cosine_similarity_dict



def plot_heatmap_comparison_violations(comparison: list) -> None:
    """
        heatmap plot based on violations for each file
        -> Each column in the heatmap is a comparison between two runs 
        Example 1: gemini-naive run1, gemini-naive run2
        Example 2: gemini-zero-shot run1, gemini-naive run1
    """
    # comparison list too long
    if len(comparison) > 6:
        raise ValueError("Too many comparisons for heatmap - max 6")
    
    experiment_ids = {}
    map_runs = {}
    for model, prompt, path in comparison:
        if model not in map_runs:
            map_runs[model] = 1

        experiment_id = str(hash(f"{model}{prompt}{path}"))
        experiment_ids[experiment_id] = {
            "model": model[0:1],
            "prompt": prompt[0:1],
            "path": path,
            "date": path.split(os.sep)[-1],
            "run": map_runs[model]
        }
        print(experiment_ids[experiment_id]["date"])
        map_runs[model] += 1

    # build vector space
    vector_space, rule_names = _build_vector_space(comparison)
    # calc cosine similarity for each pari
    cosine_similarity_dict = _calculate_cosine_similarity(vector_space)


    # dataframe out of dict 
    df_cosine = pd.DataFrame.from_dict(cosine_similarity_dict, orient='index').fillna(0)
    # rename columns to human readable
    df_cosine.columns = [f"{experiment_ids[col.split('_vs_')[0]]['model']}-{experiment_ids[col.split('_vs_')[0]]['prompt']}-{experiment_ids[col.split('_vs_')[0]]['run']}_vs_{experiment_ids[col.split('_vs_')[1]]['model']}-{experiment_ids[col.split('_vs_')[1]]['prompt']}-{experiment_ids[col.split('_vs_')[1]]['run']}" for col in df_cosine.columns]

    fig, ax = plt.subplots(figsize=(6, 9), constrained_layout=True)

    image = ax.imshow(df_cosine.values, cmap='hot', vmin=0, vmax=1, aspect='auto')

    ax.set_xticks(np.arange(df_cosine.shape[1]), labels=df_cosine.columns, rotation=45, ha="right", fontsize=8)

    cbar = fig.colorbar(image, ax=ax, fraction=0.025, pad=0.02)
    cbar.set_label("Cosine Similarity (0 … 1)", fontsize=9)

    plt.xticks(range(df_cosine.shape[1]), df_cosine.columns, rotation=45, ha='right', fontsize=8)
    plt.yticks(range(df_cosine.shape[0]), df_cosine.index, fontsize=7)
    plt.title('Pairwise Cosine Similarity per Screenshot across Different Models')
    plt.show()

    pass



# Test
if __name__ == "__main__":

    result_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "Results", "accessibility", "average")

    # 1. General Comparison Data (Average)
    # 1.1 per Model and Prompt Strategy
    comparison_data_average_gemini = [
        ("gemini", "naive", os.path.join(result_path, "gemini_naive_average_results.json")),
        ("gemini", "zero-shot", os.path.join(result_path, "gemini_zero-shot_average_results.json")),
        ("gemini", "few-shot", os.path.join(result_path, "gemini_few-shot_average_results.json")),
        ("gemini", "reason", os.path.join(result_path, "gemini_reason_average_results.json")),
        ("gemini", "iterative_naive", os.path.join(result_path, "gemini_iterative_naive_average_results.json")),
        ("gemini", "iterative_naive_refine_1", os.path.join(result_path, "gemini_iterative_naive_refine_1_average_results.json")),
        ("gemini", "iterative_naive_refine_2", os.path.join(result_path, "gemini_iterative_naive_refine_2_average_results.json")),
        ("gemini", "iterative_naive_refine_3", os.path.join(result_path, "gemini_iterative_naive_refine_3_average_results.json")),
        ("gemini", "composite_naive_refine", os.path.join(result_path, "gemini_composite_naive_refine_average_results.json")),
        ("gemini", "agent_naive_refine", os.path.join(result_path, "gemini_agent_naive_refine_average_results.json")),
    ]

    comparison_data_average_openai = [
        ("openai", "naive", os.path.join(result_path, "openai_naive_average_results.json")),
        ("openai", "zero-shot", os.path.join(result_path, "openai_zero-shot_average_results.json")),
        ("openai", "few-shot", os.path.join(result_path, "openai_few-shot_average_results.json")),
        ("openai", "reason", os.path.join(result_path, "openai_reason_average_results.json")),
        ("openai", "iterative_naive", os.path.join(result_path, "openai_iterative_naive_average_results.json")),
        ("openai", "iterative_naive_refine_1", os.path.join(result_path, "openai_iterative_naive_refine_1_average_results.json")),
        ("openai", "iterative_naive_refine_2", os.path.join(result_path, "openai_iterative_naive_refine_2_average_results.json")),
        ("openai", "iterative_naive_refine_3", os.path.join(result_path, "openai_iterative_naive_refine_3_average_results.json")),
        ("openai", "composite_naive_refine", os.path.join(result_path, "openai_composite_naive_refine_average_results.json")),
        ("openai", "agent_naive_refine", os.path.join(result_path, "openai_agent_naive_refine_average_results.json")),
    ]

    comparison_data_average_qwen = [
        ("qwen", "naive", os.path.join(result_path, "qwen_naive_average_results.json")),
        ("qwen", "zero-shot", os.path.join(result_path, "qwen_zero-shot_average_results.json")),
        ("qwen", "few-shot", os.path.join(result_path, "qwen_few-shot_average_results.json")),
        ("qwen", "reason", os.path.join(result_path, "qwen_reason_average_results.json")),
        ("qwen", "iterative_naive", os.path.join(result_path, "qwen_iterative_naive_average_results.json")),
        ("qwen", "iterative_naive_refine_1", os.path.join(result_path, "qwen_iterative_naive_refine_1_average_results.json")),
        ("qwen", "iterative_naive_refine_2", os.path.join(result_path, "qwen_iterative_naive_refine_2_average_results.json")),
        ("qwen", "iterative_naive_refine_3", os.path.join(result_path, "qwen_iterative_naive_refine_3_average_results.json")),
        ("qwen", "composite_refine", os.path.join(result_path, "qwen_composite_naive_refine_average_results.json")),
        ("qwen", "agent_refine", os.path.join(result_path, "qwen_agent_naive_refine_average_results.json")),
    ]

    comparison_data_average_llava = [
        ("llava", "naive", os.path.join(result_path, "llava_naive_average_results.json")),
        ("llava", "zero-shot", os.path.join(result_path, "llava_zero-shot_average_results.json")),
        ("llava", "few-shot", os.path.join(result_path, "llava_few-shot_average_results.json")),
        ("llava", "reason", os.path.join(result_path, "llava_reason_average_results.json")),
    ]

    comparison_data_average_all = comparison_data_average_gemini + comparison_data_average_openai + comparison_data_average_qwen + comparison_data_average_llava

    # plot_bar_average_violations(comparison_data_average_qwen)
    # plot_cake_average_violations(comparison_data_average_openai[5][2])
    # map_severity_distr = get_severity_distribution(comparison_data_average_llava)


    # 2. Specific (per File) Comparison Data
    output_path = os.path.join(os.path.dirname(__file__), "..", "..", "Output")

    comparison_data_specific_gemini = [
        # ("gemini", "naive", os.path.join(output_path, "gemini", "accessibility", "naive", "2025-06-18-10-18")),
        # ("gemini", "naive", os.path.join(output_path, "gemini", "accessibility", "naive", "2025-06-18-11-24")),
        # ("gemini", "naive", os.path.join(output_path, "gemini", "accessibility", "naive", "2025-06-18-11-53")),
        # ("gemini", "zero-shot", os.path.join(output_path, "gemini", "accessibility", "zero-shot", "2025-06-18-13-25")),
        # ("gemini", "zero-shot", os.path.join(output_path, "gemini", "accessibility", "zero-shot", "2025-06-18-14-29")),
        # ("gemini", "zero-shot", os.path.join(output_path, "gemini", "accessibility", "zero-shot", "2025-06-18-15-40")),
        # ("gemini", "reason", os.path.join(output_path, "gemini", "accessibility", "reason", "2025-06-18-16-24")),
        # ("gemini", "reason", os.path.join(output_path, "gemini", "accessibility", "reason", "2025-06-18-17-38")),
        # ("gemini", "reason", os.path.join(output_path, "gemini", "accessibility", "reason", "2025-06-18-20-49")),
        # ("gemini", "iterative", os.path.join(output_path, "gemini", "accessibility", "iterative", "2025-06-18-21-10")),
        # ("gemini", "iterative", os.path.join(output_path, "gemini", "accessibility", "iterative", "2025-06-19-07-33")),
        # ("gemini", "iterative", os.path.join(output_path, "gemini", "accessibility", "iterative", "2025-06-19-10-46")),
        ("gemini", "iterative_refine_1", os.path.join(output_path, "gemini", "accessibility", "iterative_refine_1", "2025-06-18-21-10")),
        ("gemini", "iterative_refine_1", os.path.join(output_path, "gemini", "accessibility", "iterative_refine_1", "2025-06-19-07-33")),
        ("gemini", "iterative_refine_1", os.path.join(output_path, "gemini", "accessibility", "iterative_refine_1", "2025-06-19-10-46")),
    ]


    comparison_data_specific_both= [
        ("openai", "naive", os.path.join(output_path, "openai", "accessibility", "naive", "2025-06-19-15-41")),
        ("openai", "naive", os.path.join(output_path, "openai", "accessibility", "naive", "2025-06-19-16-53")),
        ("openai", "naive", os.path.join(output_path, "openai", "accessibility", "naive", "2025-06-19-19-05")),
        ("gemini", "naive", os.path.join(output_path, "gemini", "accessibility", "naive", "2025-06-18-10-18")),
        ("gemini", "naive", os.path.join(output_path, "gemini", "accessibility", "naive", "2025-06-18-11-24")),
        ("gemini", "naive", os.path.join(output_path, "gemini", "accessibility", "naive", "2025-06-18-11-53")),
        # ("openai", "zero-shot", os.path.join(output_path, "openai", "accessibility", "zero-shot", "2025-06-20-09-55")),
        # ("openai", "zero-shot", os.path.join(output_path, "openai", "accessibility", "zero-shot", "2025-06-20-11-10")),
        # ("openai", "zero-shot", os.path.join(output_path, "openai", "accessibility", "zero-shot", "2025-06-20-12-33")),
        # ("gemini", "zero-shot", os.path.join(output_path, "gemini", "accessibility", "zero-shot", "2025-06-18-13-25")),
        # ("gemini", "zero-shot", os.path.join(output_path, "gemini", "accessibility", "zero-shot", "2025-06-18-14-29")),
        # ("gemini", "zero-shot", os.path.join(output_path, "gemini", "accessibility", "zero-shot", "2025-06-18-15-40")),
        # ("openai", "reason", os.path.join(output_path, "openai", "accessibility", "reason", "2025-06-20-15-39")),
        # ("openai", "reason", os.path.join(output_path, "openai", "accessibility", "reason", "2025-06-20-17-42")),
        # ("openai", "reason", os.path.join(output_path, "openai", "accessibility", "reason", "2025-06-20-19-43")),
        # ("gemini", "reason", os.path.join(output_path, "gemini", "accessibility", "reason", "2025-06-18-16-24")),
        # ("gemini", "reason", os.path.join(output_path, "gemini", "accessibility", "reason", "2025-06-18-17-38")),
        # ("gemini", "reason", os.path.join(output_path, "gemini", "accessibility", "reason", "2025-06-18-20-49")),
        # ("openai", "iterative", os.path.join(output_path, "openai", "accessibility", "iterative", "2025-06-21-11-04")),
        # ("openai", "iterative", os.path.join(output_path, "openai", "accessibility", "iterative", "2025-06-21-15-32")),
        # ("openai", "iterative", os.path.join(output_path, "openai", "accessibility", "iterative", "2025-06-21-19-26")),
        # ("gemini", "iterative", os.path.join(output_path, "gemini", "accessibility", "iterative", "2025-06-18-21-10")),
        # ("gemini", "iterative", os.path.join(output_path, "gemini", "accessibility", "iterative", "2025-06-19-07-33")),
        # ("gemini", "iterative", os.path.join(output_path, "gemini", "accessibility", "iterative", "2025-06-19-10-46")),
        # ("openai", "iterative_refine_1", os.path.join(output_path, "openai", "accessibility", "iterative_refine_1", "2025-06-21-11-04")),
        # ("openai", "iterative_refine_1", os.path.join(output_path, "openai", "accessibility", "iterative_refine_1", "2025-06-21-15-32")),
        # ("openai", "iterative_refine_1", os.path.join(output_path, "openai", "accessibility", "iterative_refine_1", "2025-06-21-19-26")),
        # ("gemini", "iterative_refine_1", os.path.join(output_path, "gemini", "accessibility", "iterative_refine_1", "2025-06-18-21-10")),
        # ("gemini", "iterative_refine_1", os.path.join(output_path, "gemini", "accessibility", "iterative_refine_1", "2025-06-19-07-33")),
        # ("gemini", "iterative_refine_1", os.path.join(output_path, "gemini", "accessibility", "iterative_refine_1", "2025-06-19-10-46")),
    ]
    plot_heatmap_comparison_violations(comparison_data_specific_both)



