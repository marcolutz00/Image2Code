import os 
import sys
from copy import deepcopy
from difflib import SequenceMatcher
import pandas as pd
from scipy.optimize import linear_sum_assignment
from bs4 import BeautifulSoup
import uuid
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import Benchmarks.ocr_free_utils as ocr_free_utils
import Benchmarks.visual_score as visual_score
import Utils.utils_general as utils_general
import Utils.utils_iterative_prompt as utils_iterative_prompt

BENCHMARKS_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'Benchmarks')


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



def _build_score_matrix(df1: pd.DataFrame, df2: pd.DataFrame):
    """
        In order to make sure to find a 1:1 match with the best fitting score, 
        we need a score matrix and use hungarian algorihtm.
    """
    n = len(df1)
    m = len(df2)


    score_matrix = np.zeros((n, m),dtype=float)

    for index1, row1 in df1.iterrows():
        for index2, row2 in df2.iterrows():
            text_similarity = _text_similarity(row1["html_snippet"], row2["html_snippet"])
            wcag_obj_similarity = 1.0 if (
                row1["wcag_id"] == row2["wcag_id"]
                and row1["wcag_url"] == row2["wcag_url"]
            ) else 0.0
            parsed_snippet_text_similarity= _text_similarity(
                row1["parsed_snippet"]["text"], row2["parsed_snippet"]["text"]
            )
            parsed_snippet_tag_similarity = _text_similarity(row1['parsed_snippet']['tag'], row2['parsed_snippet']["tag"]) if row1['parsed_snippet']["tag"] and row2['parsed_snippet']["tag"] else 0
            same_wcag_format = 1 if (row1['violation_id'] == row2['violation_id'] and 
                                     ((
                                         row1['violation_id'].startswith("https") and row2['violation_id'].startswith("https")) 
                                         or 
                                         (not row1['violation_id'].startswith("https") and not row2['violation_id'].startswith("https")))
                                    ) else 0
            violation_message_similarity = _text_similarity(
                row1["violation_message"], row2["violation_message"]
            )
            source_similarity = 1.0 if (row1["source"] == row2["source"]) else 0.0

            # calculate score
            score = (violation_message_similarity * 2 + text_similarity * 4 + wcag_obj_similarity + same_wcag_format + parsed_snippet_text_similarity + parsed_snippet_tag_similarity + 2 * source_similarity) / 12

            score_matrix[index1, index2] = score
    
    return score_matrix



def _find_best_matches(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    """
    """

    score_matrix = _build_score_matrix(df1, df2)

    # threshold for matching
    threshold = 0.75

    n, m = score_matrix.shape

    if n != m:
        max_amount = max(n, m)
        padded = np.zeros((max_amount, max_amount))
        padded[:n, :m] =  score_matrix
        score_matrix = padded

    row_index, column_index = linear_sum_assignment(-score_matrix)

    for row, column in zip(row_index, column_index):
        if row < len(df1) and column < len(df2):
            id1, id2 = df1.at[row, "unique_id"], df2.at[column, "unique_id"]
            score = float(score_matrix[row, column])

            # Only match if higher than theshiold
            if score > threshold:
                df1.at[row, "matched_to"] = id2
                df1.at[row, "match_score"] = score
                df2.at[column, "matched_to"] = id1
                df2.at[column, "match_score"] = score

    # Concatenate dataframes
    df_combined = pd.concat([df1, df2], ignore_index=True)

    return df_combined



def _structure_violations(violations: list, model: str, prompt: str, file: str) -> pd.DataFrame:
    """
    """

    structured_violations = []

    violation_snippets = utils_iterative_prompt.extract_issues_tools(violations, source_show=True)

    for snippet in violation_snippets:
        snippet_data = snippet["snippet"]
        snippet_id = snippet["id"]
        snippet_message = snippet["message"]
        snippet_impact = snippet["impact"]
        snippet_source = snippet["source"]

        wcag_object = _get_wcag_object(snippet_id)

        # unique hash
        unique_hash = uuid.uuid4().hex

        structured_violations.append({
            "unique_id": unique_hash,
            "file_id": file,
            "model": model,
            "prompt": prompt,
            "wcag_id": wcag_object["wcag_id"],
            "wcag_url": wcag_object["url"],
            "source": snippet_source,
            "violation_id": snippet_id,
            "violation_message": snippet_message,
            "impact": snippet_impact,
            "html_snippet": snippet_data,
            "parsed_snippet": _parse_html_snippet(snippet_data),
            "matched_to": None,
            "match_score": 0.0
        })

    return pd.DataFrame(structured_violations)

def _match_violations_external(information1: list, information2: list) -> pd.DataFrame:
    """

    """

    accessibility1_path, model1, prompt1 = information1
    accessibility2_path, model2, prompt2 = information2

    violations1 = utils_general.read_json(accessibility1_path) 
    violations2 = utils_general.read_json(accessibility2_path) 

    base_file1 = accessibility1_path.split("/")[-1].split('.')[0]
    base_file2 = accessibility2_path.split("/")[-1].split('.')[0]

    df_violations1 = _structure_violations(violations1, model1, prompt1, base_file1)
    df_violations2 = _structure_violations(violations2, model2, prompt2, base_file2)

    df_matched_violations = _find_best_matches(df_violations1, df_violations2)

    print(df_matched_violations.shape)

    print(len(df_matched_violations[df_matched_violations['matched_to'].notnull()]))
    print(df_matched_violations)


    return df_matched_violations




def _export_df_to_excel(df: pd.DataFrame, output_path: str, information1: list, information2: list) -> None:
    """
    Exports dataframe to excel
    """
    file_id1, model1, prompt1 = information1
    file_id2, model2, prompt2 = information2

    output_file = os.path.join(output_path, f"{model1}_{prompt1}_{model2}_{prompt2}_analysis.xlsx")
    df.to_excel(output_file, index=False)

    print(f"DataFrame exported : {output_file}")



def create_analysis_df(pack1: list, pack2: list) -> pd.DataFrame:
    """
    Creates a Dataframe which will be used for analysis purposes
    Columns: File_id, Model, Prompt, Wcag_id, name, impact, html_snippet
    """
    accessibility1_path, model1, prompt1 = pack1
    accessibility2_path, model2, prompt2 = pack2


    information1 = [accessibility1_path, model1, prompt1]
    information2 = [accessibility2_path, model2, prompt2]

    df_violations_merge = _match_violations_external(information1, information2)

    return df_violations_merge


def start_qualitative_analysis(info1: list, info2: list) -> pd.DataFrame:
    """
    xxx
    """
    full_df = pd.DataFrame()

    accessibility_path1, model1, prompt1 = info1
    accessibility_path2, model2, prompt2 = info2


    for file in os.listdir(accessibility_path1):
        if os.path.isdir(file) and not file.endswith('.json'):
            continue

        accessibility1_path_file = os.path.join(accessibility_path1, file)
        accessibility2_path_file = os.path.join(accessibility_path2, file)

        analysis_df = create_analysis_df(
            [accessibility1_path_file, model1, prompt1],
            [accessibility2_path_file, model2, prompt2]
        )

        print(analysis_df)

        # concat dataframes
        full_df = pd.concat([full_df, analysis_df], ignore_index=True)

    

    _export_df_to_excel(full_df, os.path.dirname(__file__), info1, info2)

    return full_df






# Test
if __name__ == "__main__":
    model = "gemini"
    prompt = "naive"

    data_path = os.path.join(os.path.dirname(__file__), '..')
    input_path = os.path.join(data_path, "Input")
    output_path = os.path.join(data_path, "Output")

    # Example paths
    accessibility1_path = os.path.join(input_path, 'accessibility')

    accessibility1_naive_path = os.path.join(output_path, 'gemini', 'accessibility', 'naive', '2025-06-18-11-53')
    accessibility1_reason_path = os.path.join(output_path, 'gemini', 'accessibility', 'reason', '2025-06-18-16-24')

    pack1 = [accessibility1_naive_path, model, prompt]
    pack2 = [accessibility1_reason_path, model, "reason"]

    df_analysis = start_qualitative_analysis(pack1, pack2)


    










    