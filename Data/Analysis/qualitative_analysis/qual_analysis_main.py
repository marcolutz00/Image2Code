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



def start_qualitative_analysis(list_paths):
    """
    Start qualitative analysis
    """

    map_landmarks = {}
    map_font_size_color_contrast = {}
    map_background_colors = {}
    list_complexity_structure = []
    map_complexity_datasets = {}

    for name, path in list_paths.items():
        print(f"Processing {name}")
        html_files = [f for f in utils_dataset.sorted_alphanumeric(os.listdir(path)) if f.endswith('.html')]
        model_name = name.split("_")[0]
 
        for file in html_files:
            print("Processing file:", file)
            html_path = os.path.join(path, file)

            # compare complexity per dataset (H1: "Dataset 2 is more complex than dataset 1,so causing more violations.")
            complexity.estimate_complexity_datasets(map_complexity_datasets, html_path, model_name)

            # get complexity and violations per file
            # complexity.estimate_complexity_structure(list_complexity_structure, html_path, model_name)

            # compare landmark structure (H1: "Landmark & Region Tags are not often set. However, there are many comparable structures, yet causing violations.")
            # landmarks.check_elements_after_body(map_landmarks, html_path, model_name)

            # get amount of small, and large fonts (H1: "Pages with more small fonts have more color contrast violations")
            # default_background_color = color_analysis.analyze_color_contrast(html_path, map_font_size_color_contrast, model_name)

            # if map_background_colors.get(name) is None:
            #     map_background_colors[name] = []

            # map_background_colors[name].append(default_background_color)
    

    # calculate correlation (H1: "Correlation between complexity (DOM-Length) and amount of xyz violations")
    df_complexity_structure = pd.DataFrame(list_complexity_structure)
    stats.correlation(df_complexity_structure, groupby_col="model", x_col="amount_nodes", y_col="amount_landmark_violations")


    # get brightness differences between background colors (H1: "Differences in backgroudn colors between models")
    color_results = color_analysis.get_brightness_differences(list_paths, map_background_colors)


    
    return map_landmarks, map_font_size_color_contrast, map_background_colors, color_results, map_complexity_datasets

    



if __name__ == "__main__":
    curr_path = Path(__file__).parent

    list_paths = {
        "gemini_naive_1": curr_path.parent.parent / "Output" / "gemini" / "html" / "naive" / "2025-06-18-10-18",
        "gemini_naive_2": curr_path.parent.parent / "Output" / "gemini" / "html" / "naive" / "2025-06-18-11-24",
        "gemini_naive_3": curr_path.parent.parent / "Output" / "gemini" / "html" / "naive" / "2025-06-18-11-53",
        "gemini_few_shot_1": curr_path.parent.parent / "Output" / "gemini" / "html" / "few-shot" / "2025-06-29-09-55",
        "gemini_few_shot_2": curr_path.parent.parent / "Output" / "gemini" / "html" / "few-shot" / "2025-06-29-10-41",
        "gemini_few_shot_3": curr_path.parent.parent / "Output" / "gemini" / "html" / "few-shot" / "2025-06-29-11-21",
        "gemini_zero_shot_1": curr_path.parent.parent / "Output" / "gemini" / "html" / "zero-shot" / "2025-06-18-13-25",
        "gemini_zero_shot_2": curr_path.parent.parent / "Output" / "gemini" / "html" / "zero-shot" / "2025-06-18-14-29",
        "gemini_zero_shot_3": curr_path.parent.parent / "Output" / "gemini" / "html" / "zero-shot" / "2025-06-18-15-40",
        "gemini_reason_1": curr_path.parent.parent / "Output" / "gemini" / "html" / "reason" / "2025-06-18-16-24",
        "gemini_reason_2": curr_path.parent.parent / "Output" / "gemini" / "html" / "reason" / "2025-06-18-17-38",
        "gemini_reason_3": curr_path.parent.parent / "Output" / "gemini" / "html" / "reason" / "2025-06-18-20-49",
        
        "openai_naive_1": curr_path.parent.parent / "Output" / "openai" / "html" / "naive" / "2025-06-19-15-41",
        "openai_naive_2": curr_path.parent.parent / "Output" / "openai" / "html" / "naive" / "2025-06-19-16-53",
        "openai_naive_3": curr_path.parent.parent / "Output" / "openai" / "html" / "naive" / "2025-06-19-19-05",
        "openai_few_shot_1": curr_path.parent.parent / "Output" / "openai" / "html" / "few-shot" / "2025-06-30-20-08",
        "openai_few_shot_2": curr_path.parent.parent / "Output" / "openai" / "html" / "few-shot" / "2025-06-30-20-39",
        "openai_few_shot_3": curr_path.parent.parent / "Output" / "openai" / "html" / "few-shot" / "2025-06-30-21-49",
        "openai_zero_shot_1": curr_path.parent.parent / "Output" / "openai" / "html" / "zero-shot" / "2025-06-20-09-55",
        "openai_zero_shot_2": curr_path.parent.parent / "Output" / "openai" / "html" / "zero-shot" / "2025-06-20-11-10",
        "openai_zero_shot_3": curr_path.parent.parent / "Output" / "openai" / "html" / "zero-shot" / "2025-06-20-12-33",
        "openai_reason_1": curr_path.parent.parent / "Output" / "openai" / "html" / "reason" / "2025-06-20-15-39",
        "openai_reason_2": curr_path.parent.parent / "Output" / "openai" / "html" / "reason" / "2025-06-20-17-42",
        "openai_reason_3": curr_path.parent.parent / "Output" / "openai" / "html" / "reason" / "2025-06-20-19-43",
    }

    map_landmarks, map_font_size_color_contrast, map_background_colors, color_results, map_complexity_datasets = start_qualitative_analysis(list_paths)

    # Export results to excel
    # utils_general.export_dict_to_excel(map_landmarks, "landmarks", curr_path / "data" / "landmark_qualitative_analysis.xlsx")
    # utils_general.export_dict_to_excel(map_font_size_color_contrast, "color_contrast", curr_path / "data" / "colorcontrast_qualitative_analysis.xlsx")
    # utils_general.export_dict_to_excel(map_background_colors, "background_colors", curr_path / "data" / "background_qualitative_analysis.xlsx")
    # utils_general.export_dict_to_excel(color_results, "color_runs", curr_path / "data" / "colorbrighter_qualitative_analysis.xlsx")
    utils_general.export_dict_to_excel(map_complexity_datasets, "complexity_datasets", curr_path / "data" / "complexity_datasets_qualitative_analysis.xlsx")

    print("Done")