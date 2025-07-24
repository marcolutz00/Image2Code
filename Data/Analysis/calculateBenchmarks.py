import os
import json
from pathlib import Path
from statistics import mean
from collections import Counter
import matplotlib.pyplot as plt


# DATE = '2025-06-29-16-32'
# MODEL = 'gemini' # gemini, openai, llama, qwen
# PROMPTING_STRATEGY = 'composite_refine'  # naive, zero-shot, few-shot, reason, iterative, iterative_refine_1, iterative_refine_2, iterative_refine_3, composite, composite_refine

# CURR_DIR = os.path.dirname(os.path.realpath(__file__))
# INSIGHTS_DIR = os.path.join(CURR_DIR, '..', 'Output', MODEL, 'insights', PROMPTING_STRATEGY, DATE)
# OUTPUT_DIR = os.path.join(CURR_DIR, '..', '..', 'Results', 'benchmarks')


def _analyze_overview_files(directory):
    """
        Reads all overview_*.json files and creates a table with IR / IW-IR
        Both for automatic and manual checks.
        Creates a box plot for the distribution.
    """
    ir_values = []
    counter_files = 0
    for fname in sorted(os.listdir(directory)):
        # Skip if dir
        if os.path.isdir(os.path.join(directory, fname)):
            continue

        
        # Test for datasets
        # number = fname.split("_")[1]
        # number = number.split(".")[0]
        # if number.isdigit() and int(number) < 29:
        #     continue

        if fname.startswith("overview_") and fname.endswith(".json"):
            with open(os.path.join(directory, fname), encoding="utf-8") as fh:
                data = json.load(fh)

            counter_files += 1

            ir_values.append({
                "file": fname,
                "auto_status": data["overall_status"]["automatic"],
                "auto_ir": data["benchmark"]["automatic_ir"],
                "auto_iwir": data["benchmark"]["automatic_iw-ir"],

            })

    if not ir_values:
        print("No file 'overview_*' found.")
        return


    # boxplot (can be deleted later)
    plt.figure(figsize=(8, 6))
    plt.boxplot(
        [
            [r["auto_ir"]    for r in ir_values],
            [r["auto_iwir"]  for r in ir_values],
        ],
        labels=["Auto IR", "Auto IW-IR"],
        showmeans=True, 
    )
    plt.ylabel("Rate")
    plt.title("Distribution of Benchmarks (IR & IW-IR)")
    plt.grid(axis="y")
    plt.tight_layout()
    plt.show()


    return {
        "files_processed": len(ir_values),
        "mean_ir": mean([r["auto_ir"] for r in ir_values]),
        "mean_iwir": mean([r["auto_iwir"] for r in ir_values]),
        "status_counts": Counter([r["auto_status"] for r in ir_values]),
    }


def _analyze_benchmark_files(directory):
    """
        Reads all benchmark_*.json files and creates a table with IR / IW-IR
        Both for automatic and manual checks.
        Creates a box plot for the distribution.
    """
    metrics = {
        "final_score": [],
        "final_size_score": [],
        "final_matched_text_score": [],
        "final_position_score": [],
        "final_text_color_score": [],
        "final_clip_score": [],
    }

    for fname in sorted(os.listdir(directory)):
        # Skip if dir
        if os.path.isdir(os.path.join(directory, fname)):
            continue

        # Test for datasets
        # number = fname.split("_")[1]
        # number = number.split(".")[0]
        # if number.isdigit() and int(number) < 29:
        # if number.isdigit() and int(number) > 28:
        #     continue

        if fname.startswith("benchmark_") and fname.endswith(".json"):
            with open(os.path.join(directory, fname), encoding="utf-8") as fh:
                data = json.load(fh)

            for key in metrics.keys():
                if key in data:
                    metrics[key].append(float(data[key]))





    if not metrics["final_score"]:
        print("No file 'benchmark_*' found.")
        return


    result = {f"mean_{k}": mean(v) for k, v in metrics.items()}
    result["files_analyzed"] = len(metrics["final_score"])
    return result



def start_calculcations(model, prompting_strategy, date, insights_dir, results_path):
    """
        Start the calculations for benchmarks
    """
    print("Start calculations for benchmarks...")
    overview_values = _analyze_overview_files(insights_dir)
    benchmark_values = _analyze_benchmark_files(insights_dir)

    if overview_values and benchmark_values:
        combination = {
            "model": model,
            "prompting_strategy": prompting_strategy,
            "date": date,
            "overview": overview_values,
            "benchmarks": benchmark_values
        }

        output_path_analysis = os.path.join(results_path, f"{model}_{prompting_strategy}_analysis_benchmarks_{date}.json")
        with open(output_path_analysis, "w", encoding="utf-8") as fh:
            json.dump(combination, fh, indent=2)

    elif overview_values and not model and not prompting_strategy:

        output_path_analysis = os.path.join(results_path, f"input_analysis_benchmarks.json")
        with open(output_path_analysis, "w", encoding="utf-8") as fh:
            json.dump(overview_values, fh, indent=2)

    else:
        print("No data found")

    
def start_process(model, prompting_strategy, date):
    """
    """
    current_path = Path(__file__).resolve().parent
    output_path = current_path.parent / "Output"
    insights_dir = output_path / model / "insights"
    results_path = current_path.parent.parent / "Results" / "benchmarks"

    if "composite" in prompting_strategy or "iterative" in prompting_strategy or "agent" in prompting_strategy:
        base_name_strat = prompting_strategy.split("_")[0]
        insight_dirs_strats = [d for d in os.listdir(insights_dir) if d.startswith(base_name_strat)]

        for prompt_strat in insight_dirs_strats:
            insight_dir_path =  insights_dir / prompt_strat / date
            start_calculcations(model, prompt_strat, date, insight_dir_path, results_path)
    else:
        insight_dir_path = insights_dir / prompting_strategy / date
        start_calculcations(model, prompting_strategy, date, insight_dir_path, results_path)


# analyze_overview_files(r"..\Input\insights")
if __name__ == "__main__":
    print("asd")
    
    # overview_values = analyze_overview_files(INSIGHTS_DIR)
    # benchmark_values = analyze_benchmark_files(INSIGHTS_DIR)
    # combination = {
    #     "model": MODEL,
    #     "prompting_strategy": PROMPTING_STRATEGY,
    #     "date": DATE,
    #     "overview": overview_values,
    #     "benchmarks": benchmark_values
    # }


    # output_path_analysis = os.path.join(OUTPUT_DIR, f"{MODEL}_{PROMPTING_STRATEGY}_analysis_benchmarks_{DATE}.json")

    # with open(output_path_analysis, "w", encoding="utf-8") as fh:
    #     json.dump(combination, fh, indent=2)