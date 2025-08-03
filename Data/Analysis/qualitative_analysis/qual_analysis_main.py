from bs4 import BeautifulSoup as bs
import os
from pathlib import Path
import pandas as pd
import sys


sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

import Utils.utils_dataset as utils_dataset
import Utils.utils_general as utils_general
import Data.Analysis.qualitative_analysis.landmarks as landmarks
import Data.Analysis.qualitative_analysis.complexity as complexity
import Data.Analysis.qualitative_analysis.color as color_analysis
import Data.Analysis.qualitative_analysis.stats as stats
import Data.Analysis.qualitative_analysis.iterative_differences as iterative_differences



def start_qualitative_analysis(list_paths):
    """
    Start qualitative analysis
    """

    map_landmarks = {}
    map_font_size_color_contrast = {}
    map_background_colors = {}
    map_foreground_colors = {}
    list_complexity_structure = []
    map_complexity_datasets = {}
    map_dom_size = {}
    color_results = {}

    for name, path in list_paths.items():
        print(f"Processing {name}")
        html_files = [f for f in utils_dataset.sorted_alphanumeric(os.listdir(path)) if f.endswith('.html')]
        model_name, run_name = name.split("_", 1)
 
        for file in html_files:
            print("Processing file:", file)
            html_path = os.path.join(path, file)

            # compare complexity per dataset (H1: "Dataset 2 is more complex than dataset 1,so causing more violations.")
            # complexity.estimate_complexity_datasets(map_complexity_datasets, html_path, model_name)

            # get complexity and violations per file
            # complexity.estimate_complexity_structure(list_complexity_structure, html_path, model_name)
            complexity.get_complexity_structure(map_dom_size, html_path, model_name)

            # compare landmark structure (H1: "Landmark & Region Tags are not often set. However, there are many comparable structures, yet causing violations.")
            # landmarks.check_elements_after_body(map_landmarks, html_path, model_name)

            # compare font colors (H1: "There are similar colors which cause color contrast violations")
            # color_analysis.get_colors_in_violations(html_path, map_foreground_colors, model_name, None)

            # get amount of small, and large fonts (H1: "Pages with more small fonts have more color contrast violations")
            # default_background_color = color_analysis.analyze_color_contrast(html_path, map_font_size_color_contrast, model_name)

            # if map_background_colors.get(name) is None:
            #     map_background_colors[name] = []

            # map_background_colors[name].append(default_background_color)
    

    # calculate correlation (H1: "Correlation between complexity (DOM-Length) and amount of xyz violations")
    # df_complexity_structure = pd.DataFrame(list_complexity_structure)
    # stats.correlation(df_complexity_structure, groupby_col="model", x_col="amount_nodes", y_col="amount_landmark_violations")


    # get brightness differences between background colors (H1: "Differences in backgroudn colors between models")
    # color_results = color_analysis.get_brightness_differences(list_paths, map_background_colors)

    # Mean of dom size
    means_dom_size = {model: sum(dom_sizes)/len(dom_sizes) for model, dom_sizes in map_dom_size.items()}


    return map_landmarks, map_font_size_color_contrast, map_background_colors, color_results, map_complexity_datasets, map_foreground_colors


def start_qualitative_analysis_iterative(list_paths_iterative):
    """
    
    """

    map_difference_all = {}

    for index in range(0, len(list_paths_iterative)):
        iteration_round = index % 4
        date = list_paths_iterative[index].name.split("/")[-1]

        if iteration_round == 3:
            continue

        map_differences = {
            "added": {},
            "removed": {},
            "unchanged": {}
        }
        
        print(f"Processing {list_paths_iterative[index]}")
        html_files = [f for f in utils_dataset.sorted_alphanumeric(os.listdir(list_paths_iterative[index])) if f.endswith('.html')]

        if index + 1 >= len(list_paths_iterative):
            break
 
        for file in html_files:
            print("Processing file:", file)
            html_path1 = os.path.join(list_paths_iterative[index], file)
            accessibility_json_path1 = html_path1.replace('.html', '.json').replace('html', 'accessibility')
            html_path2 = os.path.join(list_paths_iterative[index + 1], file)
            accessibility_json_path2 = html_path2.replace('.html', '.json').replace('html', 'accessibility')

            map_differences_file = iterative_differences.calculate_differences_iterative_rounds(accessibility_json1_path=accessibility_json_path1, accessibility_json2_path=accessibility_json_path2)

            if map_differences_file is None:
                continue

            for key in map_differences_file.keys():
                for item in map_differences_file[key]:
                    if map_differences[key].get("amount") is None:
                        map_differences[key]["amount"] = 0
                    map_differences[key]["amount"] += 1
                    if map_differences[key].get(item["rule"]) is None:
                        map_differences[key][item["rule"]] = 0
                    map_differences[key][item["rule"]] += 1
        
        map_difference_all[f"{iteration_round}_{iteration_round+1}_{date}"] = map_differences
    
    return map_difference_all




if __name__ == "__main__":
    curr_path = Path(__file__).parent

    map_paths = {
        "gemini_naive_1": curr_path.parent.parent / "Output" / "gemini" / "html" / "naive" / "2025-06-18-10-18",
        "gemini_naive_2": curr_path.parent.parent / "Output" / "gemini" / "html" / "naive" / "2025-06-18-11-24",
        "gemini_naive_3": curr_path.parent.parent / "Output" / "gemini" / "html" / "naive" / "2025-06-18-11-53",
        # "gemini_zero_shot_1": curr_path.parent.parent / "Output" / "gemini" / "html" / "zero-shot" / "2025-06-18-13-25",
        # "gemini_zero_shot_2": curr_path.parent.parent / "Output" / "gemini" / "html" / "zero-shot" / "2025-06-18-14-29",
        # "gemini_zero_shot_3": curr_path.parent.parent / "Output" / "gemini" / "html" / "zero-shot" / "2025-06-18-15-40",
        # "gemini_few_shot_1": curr_path.parent.parent / "Output" / "gemini" / "html" / "few-shot" / "2025-06-29-09-55",
        # "gemini_few_shot_2": curr_path.parent.parent / "Output" / "gemini" / "html" / "few-shot" / "2025-06-29-10-41",
        # "gemini_few_shot_3": curr_path.parent.parent / "Output" / "gemini" / "html" / "few-shot" / "2025-06-29-11-21",
        # "gemini_reason_1": curr_path.parent.parent / "Output" / "gemini" / "html" / "reason" / "2025-06-18-16-24",
        # "gemini_reason_2": curr_path.parent.parent / "Output" / "gemini" / "html" / "reason" / "2025-06-18-17-38",
        # "gemini_reason_3": curr_path.parent.parent / "Output" / "gemini" / "html" / "reason" / "2025-06-18-20-49",
        
        "openai_naive_1": curr_path.parent.parent / "Output" / "openai" / "html" / "naive" / "2025-06-19-15-41",
        "openai_naive_2": curr_path.parent.parent / "Output" / "openai" / "html" / "naive" / "2025-06-19-16-53",
        "openai_naive_3": curr_path.parent.parent / "Output" / "openai" / "html" / "naive" / "2025-06-19-19-05",
        # "openai_zero_shot_1": curr_path.parent.parent / "Output" / "openai" / "html" / "zero-shot" / "2025-06-20-09-55",
        # "openai_zero_shot_2": curr_path.parent.parent / "Output" / "openai" / "html" / "zero-shot" / "2025-06-20-11-10",
        # "openai_zero_shot_3": curr_path.parent.parent / "Output" / "openai" / "html" / "zero-shot" / "2025-06-20-12-33",
        # "openai_few_shot_1": curr_path.parent.parent / "Output" / "openai" / "html" / "few-shot" / "2025-06-30-20-08",
        # "openai_few_shot_2": curr_path.parent.parent / "Output" / "openai" / "html" / "few-shot" / "2025-06-30-20-39",
        # "openai_few_shot_3": curr_path.parent.parent / "Output" / "openai" / "html" / "few-shot" / "2025-06-30-21-49",
        # "openai_reason_1": curr_path.parent.parent / "Output" / "openai" / "html" / "reason" / "2025-06-20-15-39",
        # "openai_reason_2": curr_path.parent.parent / "Output" / "openai" / "html" / "reason" / "2025-06-20-17-42",
        # "openai_reason_3": curr_path.parent.parent / "Output" / "openai" / "html" / "reason" / "2025-06-20-19-43",

        "qwen_naive_1": curr_path.parent.parent / "Output" / "qwen" / "html" / "naive" / "2025-07-08-08-34",
        "qwen_naive_2": curr_path.parent.parent / "Output" / "qwen" / "html" / "naive" / "2025-07-08-08-51",
        "qwen_naive_3": curr_path.parent.parent / "Output" / "qwen" / "html" / "naive" / "2025-07-08-09-05",
        # "qwen_zero_shot_1": curr_path.parent.parent / "Output" / "qwen" / "html" / "zero-shot" / "2025-07-08-09-14",
        # "qwen_zero_shot_2": curr_path.parent.parent / "Output" / "qwen" / "html" / "zero-shot" / "2025-07-08-09-27",
        # "qwen_zero_shot_3": curr_path.parent.parent / "Output" / "qwen" / "html" / "zero-shot" / "2025-07-08-09-40",
        # "qwen_few_shot_1": curr_path.parent.parent / "Output" / "qwen" / "html" / "few-shot" / "2025-07-08-11-45",
        # "qwen_few_shot_2": curr_path.parent.parent / "Output" / "qwen" / "html" / "few-shot" / "2025-07-08-11-57",
        # "qwen_few_shot_3": curr_path.parent.parent / "Output" / "qwen" / "html" / "few-shot" / "2025-07-08-12-08",
        # "qwen_reason_1": curr_path.parent.parent / "Output" / "qwen" / "html" / "reason" / "2025-07-08-12-29",
        # "qwen_reason_2": curr_path.parent.parent / "Output" / "qwen" / "html" / "reason" / "2025-07-08-12-40",
        # "qwen_reason_3": curr_path.parent.parent / "Output" / "qwen" / "html" / "reason" / "2025-07-09-08-35",

        "llava_naive_1": curr_path.parent.parent / "Output" / "llava" / "html" / "naive" / "2025-07-12-10-59",
        "llava_naive_2": curr_path.parent.parent / "Output" / "llava" / "html" / "naive" / "2025-07-12-12-17",
        "llava_naive_3": curr_path.parent.parent / "Output" / "llava" / "html" / "naive" / "2025-07-12-13-58",
    }

    map_paths_iterative = {
        "gemini_iterative_naive_1": curr_path.parent.parent / "Output" / "gemini" / "html" / "iterative_naive" / "2025-07-16-09-01",
        "gemini_iterative_naive_1_refine_1": curr_path.parent.parent / "Output" / "gemini" / "html" / "iterative_naive_refine_1" / "2025-07-16-09-01",
        "gemini_iterative_naive_1_refine_2": curr_path.parent.parent / "Output" / "gemini" / "html" / "iterative_naive_refine_2" / "2025-07-16-09-01",
        "gemini_iterative_naive_1_refine_3": curr_path.parent.parent / "Output" / "gemini" / "html" / "iterative_naive_refine_3" / "2025-07-16-09-01",
        "gemini_iterative_naive_2": curr_path.parent.parent / "Output" / "gemini" / "html" / "iterative_naive" / "2025-07-16-11-02",
        "gemini_iterative_naive_2_refine_1": curr_path.parent.parent / "Output" / "gemini" / "html" / "iterative_naive_refine_1" / "2025-07-16-11-02",
        "gemini_iterative_naive_2_refine_2": curr_path.parent.parent / "Output" / "gemini" / "html" / "iterative_naive_refine_2" / "2025-07-16-11-02",
        "gemini_iterative_naive_2_refine_3": curr_path.parent.parent / "Output" / "gemini" / "html" / "iterative_naive_refine_3" / "2025-07-16-11-02",
        "gemini_iterative_naive_3": curr_path.parent.parent / "Output" / "gemini" / "html" / "iterative_naive" / "2025-07-16-13-16",
        "gemini_iterative_naive_3_refine_1": curr_path.parent.parent / "Output" / "gemini" / "html" / "iterative_naive_refine_1" / "2025-07-16-13-16",
        "gemini_iterative_naive_3_refine_2": curr_path.parent.parent / "Output" / "gemini" / "html" / "iterative_naive_refine_2" / "2025-07-16-13-16",
        "gemini_iterative_naive_3_refine_3": curr_path.parent.parent / "Output" / "gemini" / "html" / "iterative_naive_refine_3" / "2025-07-16-13-16",
        
        "openai_iterative_naive_1": curr_path.parent.parent / "Output" / "openai" / "html" / "iterative_naive" / "2025-07-16-11-06",
        "openai_iterative_naive_1_refine_1": curr_path.parent.parent / "Output" / "openai" / "html" / "iterative_naive_refine_1" / "2025-07-16-11-06",
        "openai_iterative_naive_1_refine_2": curr_path.parent.parent / "Output" / "openai" / "html" / "iterative_naive_refine_2" / "2025-07-16-11-06",
        "openai_iterative_naive_1_refine_3": curr_path.parent.parent / "Output" / "openai" / "html" / "iterative_naive_refine_3" / "2025-07-16-11-06",
        "openai_iterative_naive_2": curr_path.parent.parent / "Output" / "openai" / "html" / "iterative_naive" / "2025-07-16-14-58",
        "openai_iterative_naive_2_refine_1": curr_path.parent.parent / "Output" / "openai" / "html" / "iterative_naive_refine_1" / "2025-07-16-14-58",
        "openai_iterative_naive_2_refine_2": curr_path.parent.parent / "Output" / "openai" / "html" / "iterative_naive_refine_2" / "2025-07-16-14-58",
        "openai_iterative_naive_2_refine_3": curr_path.parent.parent / "Output" / "openai" / "html" / "iterative_naive_refine_3" / "2025-07-16-14-58",
        "openai_iterative_naive_3": curr_path.parent.parent / "Output" / "openai" / "html" / "iterative_naive" / "2025-07-16-19-50",
        "openai_iterative_naive_3_refine_1": curr_path.parent.parent / "Output" / "openai" / "html" / "iterative_naive_refine_1" / "2025-07-16-19-50",
        "openai_iterative_naive_3_refine_2": curr_path.parent.parent / "Output" / "openai" / "html" / "iterative_naive_refine_2" / "2025-07-16-19-50",
        "openai_iterative_naive_3_refine_3": curr_path.parent.parent / "Output" / "openai" / "html" / "iterative_naive_refine_3" / "2025-07-16-19-50",

        "qwen_iterative_naive_1": curr_path.parent.parent / "Output" / "qwen" / "html" / "iterative_naive" / "2025-07-16-08-47",
        "qwen_iterative_naive_1_refine_1": curr_path.parent.parent / "Output" / "qwen" / "html" / "iterative_naive_refine_1" / "2025-07-16-08-47",
        "qwen_iterative_naive_1_refine_2": curr_path.parent.parent / "Output" / "qwen" / "html" / "iterative_naive_refine_2" / "2025-07-16-08-47",
        "qwen_iterative_naive_1_refine_3": curr_path.parent.parent / "Output" / "qwen" / "html" / "iterative_naive_refine_3" / "2025-07-16-08-47",
        "qwen_iterative_naive_2": curr_path.parent.parent / "Output" / "qwen" / "html" / "iterative_naive" / "2025-07-16-09-03",
        "qwen_iterative_naive_2_refine_1": curr_path.parent.parent / "Output" / "qwen" / "html" / "iterative_naive_refine_1" / "2025-07-16-09-03",
        "qwen_iterative_naive_2_refine_2": curr_path.parent.parent / "Output" / "qwen" / "html" / "iterative_naive_refine_2" / "2025-07-16-09-03",
        "qwen_iterative_naive_2_refine_3": curr_path.parent.parent / "Output" / "qwen" / "html" / "iterative_naive_refine_3" / "2025-07-16-09-03",
        "qwen_iterative_naive_3": curr_path.parent.parent / "Output" / "qwen" / "html" / "iterative_naive" / "2025-07-16-09-31",
        "qwen_iterative_naive_3_refine_1": curr_path.parent.parent / "Output" / "qwen" / "html" / "iterative_naive_refine_1" / "2025-07-16-09-31",
        "qwen_iterative_naive_3_refine_2": curr_path.parent.parent / "Output" / "qwen" / "html" / "iterative_naive_refine_2" / "2025-07-16-09-31",
        "qwen_iterative_naive_3_refine_3": curr_path.parent.parent / "Output" / "qwen" / "html" / "iterative_naive_refine_3" / "2025-07-16-09-31",
    }

    list_paths_iterative = [
        # curr_path.parent.parent / "Output" / "gemini" / "html" / "iterative_naive" / "2025-07-16-09-01",
        # curr_path.parent.parent / "Output" / "gemini" / "html" / "iterative_naive_refine_1" / "2025-07-16-09-01",
        # curr_path.parent.parent / "Output" / "gemini" / "html" / "iterative_naive_refine_2" / "2025-07-16-09-01",
        # curr_path.parent.parent / "Output" / "gemini" / "html" / "iterative_naive_refine_3" / "2025-07-16-09-01",
        # curr_path.parent.parent / "Output" / "gemini" / "html" / "iterative_naive" / "2025-07-16-11-02",
        # curr_path.parent.parent / "Output" / "gemini" / "html" / "iterative_naive_refine_1" / "2025-07-16-11-02",
        # curr_path.parent.parent / "Output" / "gemini" / "html" / "iterative_naive_refine_2" / "2025-07-16-11-02",
        # curr_path.parent.parent / "Output" / "gemini" / "html" / "iterative_naive_refine_3" / "2025-07-16-11-02",
        # curr_path.parent.parent / "Output" / "gemini" / "html" / "iterative_naive" / "2025-07-16-13-16",
        # curr_path.parent.parent / "Output" / "gemini" / "html" / "iterative_naive_refine_1" / "2025-07-16-13-16",
        # curr_path.parent.parent / "Output" / "gemini" / "html" / "iterative_naive_refine_2" / "2025-07-16-13-16",
        # curr_path.parent.parent / "Output" / "gemini" / "html" / "iterative_naive_refine_3" / "2025-07-16-13-16",
        
        # curr_path.parent.parent / "Output" / "openai" / "html" / "iterative_naive" / "2025-07-16-11-06",
        # curr_path.parent.parent / "Output" / "openai" / "html" / "iterative_naive_refine_1" / "2025-07-16-11-06",
        # curr_path.parent.parent / "Output" / "openai" / "html" / "iterative_naive_refine_2" / "2025-07-16-11-06",
        # curr_path.parent.parent / "Output" / "openai" / "html" / "iterative_naive_refine_3" / "2025-07-16-11-06",
        # curr_path.parent.parent / "Output" / "openai" / "html" / "iterative_naive" / "2025-07-16-14-58",
        # curr_path.parent.parent / "Output" / "openai" / "html" / "iterative_naive_refine_1" / "2025-07-16-14-58",
        # curr_path.parent.parent / "Output" / "openai" / "html" / "iterative_naive_refine_2" / "2025-07-16-14-58",
        # curr_path.parent.parent / "Output" / "openai" / "html" / "iterative_naive_refine_3" / "2025-07-16-14-58",
        # curr_path.parent.parent / "Output" / "openai" / "html" / "iterative_naive" / "2025-07-16-19-50",
        # curr_path.parent.parent / "Output" / "openai" / "html" / "iterative_naive_refine_1" / "2025-07-16-19-50",
        # curr_path.parent.parent / "Output" / "openai" / "html" / "iterative_naive_refine_2" / "2025-07-16-19-50",
        # curr_path.parent.parent / "Output" / "openai" / "html" / "iterative_naive_refine_3" / "2025-07-16-19-50",

        curr_path.parent.parent / "Output" / "qwen" / "html" / "iterative_naive" / "2025-07-16-08-47",
        curr_path.parent.parent / "Output" / "qwen" / "html" / "iterative_naive_refine_1" / "2025-07-16-08-47",
        curr_path.parent.parent / "Output" / "qwen" / "html" / "iterative_naive_refine_2" / "2025-07-16-08-47",
        curr_path.parent.parent / "Output" / "qwen" / "html" / "iterative_naive_refine_3" / "2025-07-16-08-47",
        curr_path.parent.parent / "Output" / "qwen" / "html" / "iterative_naive" / "2025-07-16-09-03",
        curr_path.parent.parent / "Output" / "qwen" / "html" / "iterative_naive_refine_1" / "2025-07-16-09-03",
        curr_path.parent.parent / "Output" / "qwen" / "html" / "iterative_naive_refine_2" / "2025-07-16-09-03",
        curr_path.parent.parent / "Output" / "qwen" / "html" / "iterative_naive_refine_3" / "2025-07-16-09-03",
        curr_path.parent.parent / "Output" / "qwen" / "html" / "iterative_naive" / "2025-07-16-09-31",
        curr_path.parent.parent / "Output" / "qwen" / "html" / "iterative_naive_refine_1" / "2025-07-16-09-31",
        curr_path.parent.parent / "Output" / "qwen" / "html" / "iterative_naive_refine_2" / "2025-07-16-09-31",
        curr_path.parent.parent / "Output" / "qwen" / "html" / "iterative_naive_refine_3" / "2025-07-16-09-31",
    ]


    # map_differences = start_qualitative_analysis_iterative(list_paths_iterative)
    map_landmarks, map_font_size_color_contrast, map_background_colors, color_results, map_complexity_datasets, map_foreground_colors = start_qualitative_analysis(map_paths)


    # Export results to excel
    # utils_general.export_dict_to_excel(map_landmarks, "landmarks", curr_path / "data" / "landmark_qualitative_analysis.xlsx")
    # utils_general.export_dict_to_excel(map_font_size_color_contrast, "color_contrast", curr_path / "data" / "colorcontrast_qualitative_analysis.xlsx")
    # utils_general.export_dict_to_excel(map_background_colors, "background_colors", curr_path / "data" / "background_qualitative_analysis.xlsx")
    # utils_general.export_dict_to_excel(color_results, "color_runs", curr_path / "data" / "colorbrighter_qualitative_analysis.xlsx")
    # utils_general.export_dict_to_excel(map_complexity_datasets, "complexity_datasets", curr_path / "data" / "complexity_datasets_qualitative_analysis.xlsx")
    utils_general.export_dict_to_excel(map_foreground_colors, "foreground_colors", curr_path / "data" / "foreground_qualitative_analysis.xlsx")
    # utils_general.export_dict_to_excel(map_differences, "iterative_differences", curr_path / "data" / "qwen_iterative_differences_qualitative_analysis.xlsx")

    print("Done")