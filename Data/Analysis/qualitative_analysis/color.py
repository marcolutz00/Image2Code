import pandas as pd
import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import Accessibility.color_recommendation as color_recommendation
import Data.Analysis.qualitative_analysis.font_size as font_size
import Data.Analysis.qualitative_analysis.stats as stats



def _is_color_brighter(rgb1, rb2):
    """

    """
    luminance1 = color_recommendation.perceived_brightness_rgb(rgb1)
    luminance2 = color_recommendation.perceived_brightness_rgb(rb2)

    # if bigger than brighter
    if luminance1 > luminance2:
        return 1
    elif luminance1 < luminance2:
        return -1
    else:
        return 0
    

# Hypothesis CC: default background Color different
def _get_default_background_color(df):
    """
    Check if defautl background color different (e.g. darker, lighter, etc)
    """
    backgrounds = df['background_color'].dropna()
    if backgrounds.empty:
        return None
    
    # Find the background color 
    most_frequent_bg = backgrounds.mode().iloc[0]

    return most_frequent_bg


    

def _get_color_runs(list_paths, models=("gemini", "openai")):
    """
    get all runs
    """
    if len(models) > 2:
        raise ValueError("Only two models are supported at a time")

    model = None
    runs = []
    for name, key in list_paths.items():        
        base_name = name.split("_")[0]

        if model != None and base_name != model:
            continue

        model = base_name

        for model_name in models:
            if model_name == base_name:
                continue
            runs.append((name, name.replace(model, model_name)))

    return runs


def analyze_color_contrast(html_path, map_findings_color_contrast, model_name):
    """
    Analyze possible hypothesis about color contrast
    """
    image_path = html_path.replace(".html", ".png")
    image_path = image_path.replace("html", "images")

    block_information = color_recommendation.get_recommended_colors(html_path, image_path, True)

    df = pd.DataFrame(block_information)

    if df.empty:
        print(f"No blocks found")
        return 0, 0, None
    
    # Check hypothesis
    amount_large_fonts, amount_small_fonts = font_size.calculate_size_fonts(df, image_path)
    default_background_color = _get_default_background_color(df)

    if map_findings_color_contrast.get(model_name) is None:
        map_findings_color_contrast[model_name] = {}
    
    if map_findings_color_contrast[model_name].get("amount_large_fonts") is None:
        map_findings_color_contrast[model_name]["amount_large_fonts"] = 0

    map_findings_color_contrast[model_name]["amount_large_fonts"] += amount_large_fonts

    if map_findings_color_contrast[model_name].get("amount_small_fonts") is None:
        map_findings_color_contrast[model_name]["amount_small_fonts"] = 0

    map_findings_color_contrast[model_name]["amount_small_fonts"] += amount_small_fonts

    
    return default_background_color



def get_brightness_differences(list_paths, map_background_colors):
    """
    check the brightness differencs between the background colors of models
    """
    runs = _get_color_runs(list_paths)
    color_results = {}

    for run in runs:
        name1, name2 = run
        key_name = f"{name1}_{name2}"

        if name1 not in map_background_colors or name2 not in map_background_colors:
            continue

        colors1 = map_background_colors[name1]
        colors2 = map_background_colors[name2]

        if not colors1 or not colors2:
            continue

        color_results[key_name] = {
            "color_differences": 0,
            "color1_brighter": 0,
            "color2_brighter": 0,
        }

        for color1, color2 in zip(colors1, colors2):
            if color1 is None or color2 is None:
                continue
            
            if color1 != color2:
                color_results[key_name]["color_differences"] += 1

            if _is_color_brighter(color1, color2) == 1:
                color_results[key_name]["color1_brighter"] += 1
            elif _is_color_brighter(color1, color2) == -1:
                color_results[key_name]["color2_brighter"] += 1

    return color_results


def get_colors_in_violations(html_path, map_findings_color_contrast, model_name, run_name=None):
    """
    Check which colors cause violatiosn
    """
    accessibility_path = html_path.replace(".html", ".json")
    accessibility_path = accessibility_path.replace("html", "accessibility")

    with open(accessibility_path, "r") as f:
        data = json.load(f)

    color_contrast_violations = stats.get_all_violations(data, "Color Contrast; Text;", full_output=True)

    if len(color_contrast_violations) == 0 or len(color_contrast_violations.get("issues", [])) == 0:
        return

    axe_core_violations = [issue for issue in color_contrast_violations.get("issues", []) if issue.get("source") == "axe-core"]

    # seen = set()
    for issue in axe_core_violations:
        temp = issue.get("nodes", {}).get("any", [])
        if len(temp) == 0:
            continue
        foreground_color = temp[0].get("data", {}).get("fgColor", None)
        background_color = temp[0].get("data", {}).get("bgColor", None)

        # if foreground_color in seen:
        #     continue
        # seen.add(foreground_color)

        if map_findings_color_contrast.get(model_name) is None:
            map_findings_color_contrast[model_name] = {}

        if run_name is None:
            if map_findings_color_contrast[model_name].get(foreground_color) is None:
                map_findings_color_contrast[model_name][foreground_color] = {
                    "amount_violations": 0,
                    # "background_color": {}
                }
            
            map_findings_color_contrast[model_name][foreground_color]["amount_violations"] += 1
            
        else:
            if map_findings_color_contrast[model_name].get(run_name) is None:
                map_findings_color_contrast[model_name][run_name] = {}

            if map_findings_color_contrast[model_name][run_name].get(foreground_color) is None:
                map_findings_color_contrast[model_name][run_name][foreground_color] = {
                    "amount_violations": 0,
                    # "background_color": {}
                }
            
            map_findings_color_contrast[model_name][run_name][foreground_color]["amount_violations"] += 1

        # if background_color not in map_findings_color_contrast[model_name][foreground_color]["background_color"]:
        #     map_findings_color_contrast[model_name][foreground_color]["background_color"][background_color] = 0

        # map_findings_color_contrast[model_name][foreground_color]["background_color"][background_color] += 1

