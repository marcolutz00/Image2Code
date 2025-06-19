import os 
import sys
from copy import deepcopy
from difflib import SequenceMatcher
import pandas as pd
import pathlib
from bs4 import BeautifulSoup

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import Benchmarks.ocr_free_utils as ocr_free_utils
import Benchmarks.visual_score as visual_score
import Utils.utils_general as utils_general
import Utils.utils_iterative_prompt as utils_iterative_prompt

BENCHMARKS_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'Benchmarks')



def _get_matched_blocks(image1_path: str, image2_path: str, html1_path: str, html2_path: str) -> tuple:
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


def _normalize_text(text: str) -> str:
    """
    Normalize text (lowercase, ...)
    """
    return " ".join(text.split()).strip().lower() if text else ""


def _parse_html_snippet(snippet: str):
    """
    Parse the HTML snippet
    """
    soup = BeautifulSoup(snippet, 'html.parser')
    node = soup.find()

    return {
        "tag":  node.name or "",
        "id":   node.get("id", ""),
        "cls":  " ".join(node.get("class", [])),
        "text": _normalize_text(node.get_text(" ", strip=True)),
    }

def _text_similarity(text1: str, text2: str) -> float:
    """ 
    Text similarity based on sequence Matcher
    """
    return SequenceMatcher(None, text1, text2).ratio()


def _get_wcag_object(violation_id: str):
    """
    based on the mapping, get the wcag object (url and id) based on the violation_id
    violation_id can be URL or WCAG ID
    """
    wcag_mapping_path = os.path.join(BENCHMARKS_PATH, '..', 'Accessibility', 'mappingCsAndAxeCore.json')
    wcag_mapping = utils_general.read_json(wcag_mapping_path)

    for wcag_obj in wcag_mapping:
        wcag_dict = {
            "wcag_id": wcag_obj['htmlcs_id'],
            "url": wcag_obj['axe_url']
        }

        if violation_id in wcag_obj['htmlcs_id'] and "null" not in wcag_obj['htmlcs_id']:
            return wcag_dict
        if violation_id in wcag_obj['axe_url'] and "null" not in wcag_obj['axe_url']:
            return wcag_dict


    return {
        "wcag_id": "None",
        "url": "None"
    }


def _match_blocks_and_violations(information: list, blocks: list, html: str, violations_tools: list) -> pd.DataFrame:
    """
    Match blocks with accessibility violations
    """
    file_id, model, prompt = information

    df = pd.DataFrame(columns=['File_Id', 'Block_Text', 'Violation_Tag', 'Model', 'Prompt', 'Wcag_Obj', 'Violation_Id', 'Violation_Message', 'Violation_Impact', 'Html_Snippet'])

    # define threshold for text simliarity (similar to benchmark)
    threshold_text_similarity = 0.5


    for block in blocks:
        block["normalized_text"] = _normalize_text(block['text'])

    for violation in violations_tools:
        snippet = _parse_html_snippet(violation['snippet'])

        # Matching algorithm
        best_score = 0
        best_block = None

        wcag_obj = _get_wcag_object(violation['id'])

        if snippet["text"] == "":
            df.loc[len(df)] = [file_id, "No Text", snippet["tag"], model, prompt, wcag_obj, violation['id'], violation['message'], violation['impact'], violation['snippet']]
            continue

        for index_block, block in enumerate(blocks):
            temp_score = _text_similarity(block["normalized_text"], snippet["text"])

            if temp_score > best_score:
                best_block = block
                best_score = temp_score
            
        final_block_index = index_block if best_score > threshold_text_similarity else None

        df.loc[len(df)] = [file_id, best_block['text'], snippet["tag"], model, prompt, wcag_obj, violation['id'], violation['message'], violation['impact'], violation['snippet']]
            

    return df

        




def _match_blocks_internal(information: list, blocks: list, html_path: str, accessibility_path: str) -> pd.DataFrame:
    """
    Internal: Match between blocks found and accessibility violations in one file
    merges all found components / blocks with accessibility violations into one DataFrame
    -> Functionality: Full Outer Join
    """
    html = utils_general.read_html(html_path)
    accessibility_violations = utils_general.read_json(accessibility_path)

    violations_tools = utils_iterative_prompt.extract_issues_tools(accessibility_violations)

    df_blocks_violations = _match_blocks_and_violations(information, blocks, html, violations_tools)
    
    print(df_blocks_violations)
    print(df_blocks_violations.columns)

    pass



def _match_blocks_external(info1: list, df1: pd.DataFrame, info2: list, df2: pd.DataFrame) -> pd.DataFrame:
    """
    External: Match between different files based on their dataframes
    """
    file_id1, model1, prompt1 = info1
    file_id2, model2, prompt2 = info2
    join_keys = ['File_Id', 'Block_Text', 'Wcag_Obj']

    df_final = df1.merge(df2, on=join_keys, how='outer', indicator=True, suffixes=(f'_{prompt1}-{model1}', f'_{prompt2}-{model2}'))

    return df_final


def _export_df_to_excel(df: pd.DataFrame, output_path: str, information1: list, information2: list) -> None:
    """
    Exports dataframe to excel
    """
    model1, prompt1 = information1
    model2, prompt2 = information2

    output_file = os.path.join(output_path, f"{model1}_{prompt1}_{model2}_{prompt2}_analysis.xlsx")
    df.to_excel(output_file, index=False)

    print(f"DataFrame exported : {output_file}")



def create_analysis_df(pack1: list, pack2: list, model: str, prompt: str) -> pd.DataFrame:
    """
    Creates a Dataframe which will be used for analysis purposes
    Columns: File_id, Model, Prompt, Wcag_id, name, impact, html_snippet
    """
    image1_path, html1_path, accessibility1_path = pack1
    image2_path, html2_path, accessibility2_path = pack2

    # get matching
    matching, blocks1, blocks2 = _get_matched_blocks(image1_path, image2_path, html1_path, html2_path)

    html1_base_name = html1_path.split('/')[-1].split('.')[0]
    html2_base_name = html2_path.split('/')[-1].split('.')[0]

    information1 = [html1_base_name, model, prompt]
    information2 = [html2_base_name, model, prompt]

    df_internal_1 = _match_blocks_internal(information1, blocks1, html1_path, accessibility1_path)
    df_internal_2 = _match_blocks_internal(information2, blocks2, html2_path, accessibility2_path)

    df_external_merge = _match_blocks_external(information1, df_internal_1, information2, df_internal_2)

    return  df_external_merge



# Test
if __name__ == "__main__":
    model = "gemini"
    prompt = "naive"

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

    df_analysis = create_analysis_df(pack1, pack2, model, prompt)


    










    