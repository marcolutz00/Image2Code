import os 
import sys
from copy import deepcopy
from difflib import SequenceMatcher
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import Benchmarks.ocr_free_utils as ocr_free_utils
import Benchmarks.visual_score as visual_score

BENCHMARKS_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'Benchmarks')



def get_matched_blocks(image1_path: str, image2_path: str, html1_path: str, html2_path: str) -> list:
    """
    Uses the matching algorithm which has been used in benchmarks
    -> Finds corresponding blocks in two files. Necessary for comparison
    """

    # Get blocks of both files
    blocks1 = ocr_free_utils.get_blocks_ocr_free(image1_path, html1_path)
    blocks2 = ocr_free_utils.get_blocks_ocr_free(image2_path, html2_path)

    # Merge blocks by bounding box if similar
    blocks1 = visual_score.merge_blocks_by_bbox(blocks1)
    blocks2 = visual_score.merge_blocks_by_bbox(blocks2)

    if not blocks1 or not blocks2:
        print("Qualitative Analysis: No blocks found.")
        return []
    
    # parameters similar to benchmarks
    consecutive_bones = 0.1
    window_size = 1

    blocks1, blocks2, matching = visual_score.find_possible_merge(deepcopy(blocks1), deepcopy(blocks2), consecutive_bones, window_size, False)

    filtered_matching = []
    for i, j in matching:
        text_similarity = SequenceMatcher(None, blocks1[i]['text'], blocks2[j]['text']).ratio()
        # Filter out matching with low similarity
        if text_similarity < 0.5:
            continue
        filtered_matching.append([i, j, text_similarity])
    matching = filtered_matching


    # TODO: Check i
    return matching



def create_analysis_dataframe(html1_path: str, html2_path: str, accessibility1_path: str, accessibility2_path: str) -> pd.DataFrame:
    """
    Creates a Dataframe which will be used for analysis purposes
    Columns: File_id, Model, Prompt, Wcag_id, name, impact, html_snippet
    """
    