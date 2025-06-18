import os 
import sys
from copy import deepcopy
from difflib import SequenceMatcher
import pandas as pd
import pathlib

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import Benchmarks.ocr_free_utils as ocr_free_utils
import Benchmarks.visual_score as visual_score
import Utils.utils_general as utils_general

BENCHMARKS_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'Benchmarks')



def get_matched_blocks(image1_path: str, image2_path: str, html1_path: str, html2_path: str) -> tuple:
    """
    Uses the matching algorithm which has been used in benchmarks
    -> Finds corresponding blocks in two files. Necessary for comparison
    """

    # Get blocks of both files
    blocks1 = ocr_free_utils.get_blocks_ocr_free(image1_path, html1_path)
    blocks2 = ocr_free_utils.get_blocks_ocr_free(image2_path, html2_path)

    # Merge blocks by bounding box if similar
    # blocks1 = visual_score.merge_blocks_by_bbox(blocks1)
    # blocks2 = visual_score.merge_blocks_by_bbox(blocks2)

    if not blocks1 or not blocks2:
        print("Qualitative Analysis: No blocks found.")
        return []
    
    # parameters similar to benchmarks
    consecutive_bonus = 0.1
    window_size = 1

    blocks1, blocks2, matching = visual_score.find_possible_merge(deepcopy(blocks1), deepcopy(blocks2), consecutive_bonus, window_size, False)

    filtered_matching = []
    for i, j in matching:
        text_similarity = SequenceMatcher(None, blocks1[i]['text'], blocks2[j]['text']).ratio()
        # Filter out matching with low similarity
        if text_similarity < 0.5:
            continue
        filtered_matching.append([i, j, text_similarity])
    matching = filtered_matching


    # TODO: Check if some components are not matched to anything!!!!
    return matching, blocks1, blocks2


def match_blocks_internal(blocks: list, html_path: str, accessibility_path: str) -> pd.DataFrame:
    """
    Internal: Match between blocks found and accessibility violations in one file
    merges all found components / blocks with accessibility violations into one DataFrame
    -> Functionality: Full Outer Join
    """
    html = utils_general.read_html(html_path)
    df_accessibility = pd.read_json(accessibility_path)

    print(df_accessibility)

    pass


def match_blocks_external(blocks1: list, blocks2: list, matching: list) -> pd.DataFrame:
    """
    External: Match between different files
    merges all found components / blocks with accessibility violations into one DataFrame
    -> Functionality: Full Outer Join
    """

    df_blocks = pd.DataFrame(columns=['File_Id', 'Block_Text', 'Model', 'Prompt', 'Wcag_Id', 'Violation_Name', 'Impact', 'Html_Snippet'])


def create_analysis_dataframe(pack1: list, pack2: list) -> pd.DataFrame:
    """
    Creates a Dataframe which will be used for analysis purposes
    Columns: File_id, Model, Prompt, Wcag_id, name, impact, html_snippet
    """
    image1_path, html1_path, accessibility1_path = pack1
    image2_path, html2_path, accessibility2_path = pack2

    # get matching
    matching, blocks1, blocks2 = get_matched_blocks(image1_path, image2_path, html1_path, html2_path)

    df_components = match_blocks_internal(blocks1, html1_path, accessibility1_path)



# Test
if __name__ == "__main__":
    data_path = os.path.join(os.path.dirname(__file__), '..')
    input_path = os.path.join(data_path, "Input")
    output_path = os.path.join(data_path, "Output")

    # Example paths
    image1_path = os.path.join(input_path, 'images', '1.png')
    image2_path = os.path.join(output_path, 'gemini', 'images', 'naive', '2025-06-18-11-53', '1.png')
    html1_path = os.path.join(input_path, 'html', '1.html')
    html2_path = os.path.join(output_path, 'gemini', 'html', 'naive', '2025-06-18-11-53', '1.html')
    accessibility1_path = os.path.join(input_path, 'accessibility', '1.json')
    accessibility2_path = os.path.join(output_path, 'gemini', 'accessibility', 'naive', '2025-06-18-11-53', '1.json')

    pack1 = [image1_path, html1_path, accessibility1_path]
    pack2 = [image2_path, html2_path, accessibility2_path]

    df_analysis = create_analysis_dataframe(pack1, pack2)
    print(df_analysis.head())









    