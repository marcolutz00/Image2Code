import os
import sys
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import Utils.utils_html as utils_html
import Utils.utils_general as utils_general
import Utils.utils_prompt as utils_prompt
import Utils.utils_iterative_prompt as utils_iterative_prompt
import Benchmarks.visual_score as visual_score
import Accessibility.accessibilityIssues as accessibilityIssues
import Accessibility.color_recommendation as color_recommendation


CURR_PATH = Path(__file__).resolve().parent
DATA_PATH = CURR_PATH.parent / "Data"
INPUT_PATH = DATA_PATH / "Input"
OUTPUT_PATH = DATA_PATH / "Output"



async def analyze_outputs(image, model, prompt_strategy, date):
    ''''
        Analyze outputs: 
        1. Structural Similarity. Create Accessibility-Tree, Bounding-Boxes, DOM-Similarity, Code-Quality
        2. Visual Similarity: Create Screenshots 
    '''
    # get basename
    image_name = os.path.splitext(image)[0]

    # 1. Define paths
    input_html_path = os.path.join(INPUT_PATH, 'html', f"{image_name}.html")
    input_accessibility_path = os.path.join(INPUT_PATH, 'accessibility', f"{image_name}.json")
    input_images_path = os.path.join(INPUT_PATH, 'images', f"{image_name}.png")
    input_insight_path = os.path.join(INPUT_PATH, 'insights', f"overview_{image_name}.json")

    output_html_path = os.path.join(OUTPUT_PATH, model, 'html', prompt_strategy, date, f"{image_name}.html")
    output_accessibility_path = os.path.join(OUTPUT_PATH, model, 'accessibility', prompt_strategy, date, f"{image_name}.json")
    output_images_path = os.path.join(OUTPUT_PATH, model, 'images', prompt_strategy, date, f"{image_name}.png")
    output_insight_path = os.path.join(OUTPUT_PATH, model, 'insights', prompt_strategy, date, f"overview_{image_name}.json")
    output_benchmark_path = os.path.join(OUTPUT_PATH, model, 'insights', prompt_strategy, date, f"benchmark_{image_name}.json")


    # 2. Calculate visual and structural Benchmarks
    # 2.1 get benchmarks
    input_list = [input_html_path, output_html_path, input_images_path, output_images_path]
    benchmark_score = visual_score.visual_eval_v3_multi(input_list)


    # # 2.2 Write Benchmarks to file
    utils_general.save_json(benchmark_score, output_benchmark_path)


    # 3. Analyze Accessibility Issues
    # await accessibilityIssues.enrich_with_accessibility_issues(image_name, input_html_path, input_accessibility_path, input_insight_path)
    accessibility_issues, accessibility_issues_overview = await accessibilityIssues.enrich_with_accessibility_issues(image_name, output_html_path, output_accessibility_path, output_insight_path)

    return benchmark_score, accessibility_issues, accessibility_issues_overview

async def process_image(client, image_information, prompt, model, prompt_strategy, date):
    '''
        Sends API-Call to LLM and lets it create output.
        The Output is then stored to the Output Directory
    '''
    result_raw, tokens_used = await client.generate_frontend_code(prompt, image_information)

    # Print token information
    if tokens_used != None:
        print(tokens_used)

    result_clean = utils_html.clean_html_result(result_raw)
    
    output_dir = os.path.join(OUTPUT_PATH, model, 'html', prompt_strategy, date)
    
    output_html_path = os.path.join(output_dir, f"{image_information["name"]}.html")
    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(result_clean)
    
    # print(f"Result for {image_information["name"]}.html stored here: {output_html_path}")
    
    return result_clean


async def process_image_iterative(client, model, prompt_strategy, html_input, accessibility_data, image, date, number_iterations=3):
    '''
        Improvement Strategy: Iterative
        Gets generated HTML and Accessibility Data
        Grabs the Code with Issues and sends it to LLM.
        Afterwards, the LLM will return fixed code and it will be stored in file.
    '''

    # In case no accessibility violatinos are found, no iteration needed
    if len(accessibility_data["automatic"]) == 0:
        return

    base_name = os.path.splitext(image)[0]
    generated_html = None

    for i in range(1, number_iterations + 1):
        output_base_html_path, output_base_accessibility_path, output_base_images_path, output_base_insights_path = utils_general.create_directories(OUTPUT_PATH, model, f"{prompt_strategy}_refine_{i}", date)

        html_snippets = utils_iterative_prompt.get_violation_snippets(html_input, accessibility_data)
        refine_prompt = utils_prompt.get_prompt("iterative")
        final_refine_prompt = f"{refine_prompt}\n\nViolations:\n{html_snippets}"

        generated_html = await utils_iterative_prompt.process_refinement_llm(client, final_refine_prompt)
        with open(os.path.join(output_base_html_path, f"{prompt_strategy}_refine_{i}", date, f"{base_name}.html"), "w", encoding="utf-8") as f:
            f.write(generated_html)
        
        if generated_html is None:
            html_file_path = os.path.join(output_base_html_path, f"{prompt_strategy}_refine_{i}", date, f"{base_name}.html")
            if os.path.exists(html_file_path):
                # HTML/CSS aus der Datei auslesen
                with open(html_file_path, "r", encoding="utf-8") as f:
                    generated_html = f.read()
            else:
                print(f"HTML-Datei nicht gefunden: {html_file_path}")
                generated_html = None
            
        _, accessibility_issues, accessibility_issues_overview = await analyze_outputs(image, model, f"{prompt_strategy}_refine_{i}", date)

        if accessibility_issues_overview["automatic_checks"].get("total_nodes_failed") == 0:
            print(f"Iteration {i} finished. No more accessibility issues ...")
            break

        accessibility_data = accessibility_issues
        html_input = generated_html



async def process_image_composite(client, model, prompt_strategy, html_input, accessibility_data, image_path, date):
    '''
        Improvement Strategy: Composite
        Uses accessibility violations, as well as color recommendations as input for the LLMs.
    '''

    base_name = os.path.splitext(image_path)[0]
    composite_html_path = os.path.join(OUTPUT_PATH, model, 'html', prompt_strategy, date, f"{base_name}.html")
    composite_image_path = os.path.join(OUTPUT_PATH, model, 'images', prompt_strategy, date, f"{base_name}.png")

    output_base_html_path, output_base_accessibility_path, output_base_images_path, output_base_insights_path = utils_general.create_directories(OUTPUT_PATH, model, f"{prompt_strategy}_refine", date)

    html_snippets = utils_iterative_prompt.get_violation_snippets(html_input, accessibility_data)
    color_recommendations = color_recommendation.get_recommended_colors(composite_html_path, composite_image_path)
    composite_prompt = utils_prompt.get_prompt("composite")

    final_composite_prompt = f"{composite_prompt}\n\nViolations:\n{html_snippets}\n\nColor Recommendations:\n{color_recommendations}"

    generated_html = await utils_iterative_prompt.process_refinement_llm(client, final_composite_prompt)

    with open(os.path.join(output_base_html_path, f"{prompt_strategy}_refine", date, f"{base_name}.html"), "w", encoding="utf-8") as f:
        f.write(generated_html)

        
    _, accessibility_issues, accessibility_issues_overview = await analyze_outputs(image_path, model, f"{prompt_strategy}_refine", date)
