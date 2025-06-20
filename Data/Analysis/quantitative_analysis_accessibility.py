import matplotlib.pyplot as plt
import json
import os
import sys
from copy import deepcopy
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import Utils.utils_general as utils_general


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







def plot_average_violations(comparison: list) -> None:
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



# Test
if __name__ == "__main__":
    result_path = os.path.join(os.path.dirname(__file__), "..", "..", "Results", "accessibility", "average")

    comparison_data = [
        ("gemini", "naive", os.path.join(result_path, "gemini_naive_average_results.json")),
        ("gemini", "zero-shot", os.path.join(result_path, "gemini_zero-shot_average_results.json")),
        ("gemini", "reason", os.path.join(result_path, "gemini_reason_average_results.json")),
        ("gemini", "iterative", os.path.join(result_path, "gemini_iterative_average_results.json")),
        ("gemini", "iterative_refine_1", os.path.join(result_path, "gemini_iterative_refine_1_average_results.json")),
        ("gemini", "iterative_refine_2", os.path.join(result_path, "gemini_iterative_refine_2_average_results.json")),
        ("gemini", "iterative_refine_3", os.path.join(result_path, "gemini_iterative_refine_3_average_results.json")),
    ]

    plot_average_violations(comparison_data)


