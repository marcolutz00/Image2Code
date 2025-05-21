import os
import json
from pathlib import Path
from statistics import mean
from collections import Counter
import matplotlib.pyplot as plt


CURR_DIR = os.path.dirname(os.path.realpath(__file__))
INPUT_INSIGHTS_DIR = os.path.join(CURR_DIR, '..', 'Output', 'gemini', 'insights', 'naive')


def analyze_overview_files(directory):
    """
        Reads all overview_*.json files and creates a table with IR / IW-IR
        Both for automatic and manual checks.
        Creates a box plot for the distribution.
    """
    rows = []
    for fname in sorted(os.listdir(directory)):
        # Skip if dir
        if os.path.isdir(os.path.join(directory, fname)):
            continue

        number = fname.split("_")[1]
        number = number.split(".")[0]

        # Test for datasets
        # if number.isdigit() and int(number) < 29:
        #     continue

        if fname.startswith("overview_") and fname.endswith(".json"):
            with open(os.path.join(directory, fname), encoding="utf-8") as fh:
                data = json.load(fh)

            rows.append({
                "file": fname,
                "auto_status": data["overall_status"]["automatic"],
                "manual_status":data["overall_status"]["manual"],
                "auto_ir": data["benchmark"]["automatic_ir"],
                "auto_iwir": data["benchmark"]["automatic_iw-ir"],
                "manual_ir": data["benchmark"]["manual_ir"],
                "manual_iwir": data["benchmark"]["manual_iw-ir"],
            })

    if not rows:
        print("No file 'overview_*' found.")
        return

    # Create table
    header = (
        "File".ljust(20)
        + "Auto-Status".ljust(14)
        + "Manual-Status".ljust(15)
        + "Auto IR".rjust(10)
        + "Auto IW-IR".rjust(14)
        + "Manual IR".rjust(12)
        + "Manual IW-IR".rjust(16)
    )

    seperator = "-" * len(header)
    print(header)
    print(seperator)

    for r in rows:
        print(
            f"{r['file']:<20}"
            f"{r['auto_status']:<14}"
            f"{r['manual_status']:<15}"
            f"{r['auto_ir']:>10.4f}"
            f"{r['auto_iwir']:>14.4f}"
            f"{r['manual_ir']:>12.4f}"
            f"{r['manual_iwir']:>16.4f}"
        )

    
    # Summary
    auto_status_counter   = Counter(r["auto_status"]   for r in rows)
    manual_status_counter = Counter(r["manual_status"] for r in rows)

    print("\n Summary")
    print(f"Total filest: {len(rows)}")
    print(f"Average Automatic IR     : {mean(r['auto_ir']   for r in rows):.4f}")
    print(f"Average Automatic IW-IR  : {mean(r['auto_iwir'] for r in rows):.4f}")
    print(f"Average Manual IR        : {mean(r['manual_ir']   for r in rows):.4f}")
    print(f"Average Manual IW-IR     : {mean(r['manual_iwir'] for r in rows):.4f}")
    print("\nStatus-Distribution (Automatic):", dict(auto_status_counter))
    print("Status-Distribution (Manual)   :", dict(manual_status_counter))


    # boxplot (can be deleted later)
    plt.figure(figsize=(8, 6))
    plt.boxplot(
        [
            [r["auto_ir"]    for r in rows],
            [r["auto_iwir"]  for r in rows],
            [r["manual_ir"]  for r in rows],
            [r["manual_iwir"]for r in rows],
        ],
        labels=["Auto IR", "Auto IW-IR", "Manual IR", "Manual IW-IR"],
        showmeans=True, 
    )
    plt.ylabel("Rate")
    plt.title("Distribution of Benchmarks (IR & IW-IR)")
    plt.grid(axis="y")
    plt.tight_layout()
    plt.show()


def analyze_benchmark_files(directory):
    """
        Reads all benchmark_*.json files and creates a table with IR / IW-IR
        Both for automatic and manual checks.
        Creates a box plot for the distribution.
    """
    rows = []
    counter_final_score = 0
    counter_final_size_score = 0
    counter_final_matched_text_score = 0
    counter_final_position_score = 0
    counter_final_text_color_score = 0
    counter_final_clip_score = 0

    for fname in sorted(os.listdir(directory)):
        # Skip if dir
        if os.path.isdir(os.path.join(directory, fname)):
            continue

        number = fname.split("_")[1]
        number = number.split(".")[0]

        # Test for datasets
        # if number.isdigit() and int(number) < 29:
        #     continue

        if fname.startswith("benchmark_") and fname.endswith(".json"):
            with open(os.path.join(directory, fname), encoding="utf-8") as fh:
                data = json.load(fh)

            rows.append({
                "file": fname,
                "final_score": data["final_score"],
                "final_size_score": data["final_size_score"],
                "final_matched_text_score": data["final_matched_text_score"],
                "final_position_score": data["final_position_score"],
                "final_text_color_score": data["final_text_color_score"],
                "final_clip_score": data["final_clip_score"],
            })

            counter_final_score += 1 if float(data["final_score"]) != 0 else 0
            counter_final_size_score += 1 if float(data["final_size_score"]) != 0 else 0
            counter_final_matched_text_score += 1 if float(data["final_matched_text_score"]) != 0 else 0
            counter_final_position_score += 1 if float(data["final_position_score"]) != 0 else 0
            counter_final_text_color_score += 1 if float(data["final_text_color_score"]) != 0 else 0
            counter_final_clip_score += 1 if float(data["final_clip_score"]) != 0 else 0

    if not rows:
        print("No file 'benchmark_*' found.")
        return

    # Create table
    header = (
        "File".ljust(20)
        + "final_score".ljust(14)
        + "final_size_score".ljust(15)
        + "final_matched_text_score".rjust(10)
        + "final_position_score".rjust(14)
        + "final_text_color_score".rjust(12)
        + "final_clip_score".rjust(16)
    )

    seperator = "-" * len(header)
    print(header)
    print(seperator)

    for r in rows:
        print(
            f"{r['file']:<20}"
            f"{r['final_score']:<14}"
            f"{r['final_size_score']:<15}"
            f"{r['final_matched_text_score']:>10.4f}"
            f"{r['final_position_score']:>14.4f}"
            f"{r['final_text_color_score']:>12.4f}"
            f"{r['final_clip_score']:>16.4f}"
        )

    

    print("\n Summary")
    print(f"Total filest: {len(rows)}")
    print(f"Average final_score      : {sum(float(r['final_score']) for r in rows) / counter_final_score:.4f}")
    print(f"Average final_size_score : {sum(float(r['final_size_score']) for r in rows) / counter_final_size_score:.4f}")
    print(f"Average final_matched_text_score : {sum(float(r['final_matched_text_score']) for r in rows) / counter_final_matched_text_score:.4f}")
    print(f"Average final_position_score : {sum(float(r['final_position_score']) for r in rows) / counter_final_position_score:.4f}")
    print(f"Average final_text_color_score : {sum(float(r['final_text_color_score']) for r in rows) / counter_final_text_color_score:.4f}")
    print(f"Average final_clip_score : {sum(float(r['final_clip_score']) for r in rows) / counter_final_clip_score:.4f}")



    # boxplot (can be deleted later)
    plt.figure(figsize=(8, 6))
    plt.boxplot(
        [
            [r["final_score"]    for r in rows],
            [r["final_size_score"]  for r in rows],
            [r["final_matched_text_score"]  for r in rows],
            [r["final_position_score"]for r in rows],
            [r["final_text_color_score"] for r in rows],
            [r["final_clip_score"] for r in rows],
        ],
        labels=["final_score", "final_size_score", "final_matched_text_score", "final_position_score", "final_text_color_score", "final_clip_score"],
        showmeans=True, 
    )
    plt.ylabel("Score")
    plt.title("Visual & Structural Benchmarks")
    plt.grid(axis="y")
    plt.tight_layout()
    plt.show()


# analyze_overview_files(r"..\Input\insights")
if __name__ == "__main__":
    # analyze_overview_files(INPUT_INSIGHTS_DIR)
    analyze_benchmark_files(INPUT_INSIGHTS_DIR)