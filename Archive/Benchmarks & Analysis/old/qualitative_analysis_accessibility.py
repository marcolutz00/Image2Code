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

    if node is None:
        return {
            "tag": "",
            "id": "",
            "cls": "",
            "text": ""
        }
    
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
            if source_similarity == 0.0:
                # If sources are not the same, we reduce the score
                score = (violation_message_similarity + text_similarity * 4 + wcag_obj_similarity * 2 + parsed_snippet_text_similarity * 2 + parsed_snippet_tag_similarity) / 10
            else:
                score = (violation_message_similarity * 2 + text_similarity * 4 + wcag_obj_similarity + same_wcag_format + parsed_snippet_text_similarity + parsed_snippet_tag_similarity + 2 * source_similarity) / 12

            score_matrix[index1, index2] = score
    
    return score_matrix



def _find_best_matches(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    """
    """

    score_matrix = _build_score_matrix(df1, df2)

    # threshold for matching
    threshold = 0.8

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
            "wcag_id": str(wcag_object["wcag_id"]),
            "wcag_url": str(wcag_object["url"]),
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

    one_empty = False

    df_violations1 = _structure_violations(violations1, model1, prompt1, base_file1)
    len_df_violations1 = len(df_violations1)
    df_violations2 = _structure_violations(violations2, model2, prompt2, base_file2)
    len_df_violations2 = len(df_violations2)

    # check if both dataframes not empty
    if len_df_violations1 == 0 or len_df_violations2 == 0:
        one_empty = True
    
    df_matched_violations = _find_best_matches(df_violations1, df_violations2)

    print(df_matched_violations.shape)

    if len(df_matched_violations) > 0 and 'matched_to' in df_matched_violations.columns:
        print(len(df_matched_violations[df_matched_violations['matched_to'].notnull()]))
    else:
        print("No matches found or matched_to column missing")
    print(df_matched_violations)


    return df_matched_violations, one_empty




def _export_df_to_excel(df: pd.DataFrame, output_path: str, information1: list, information2: list, prefix: str = None) -> None:
    """
    Exports dataframe to excel
    """
    path1, model1, prompt1 = information1
    path2, model2, prompt2 = information2

    date1 = path1.split("/")[-1]
    date2 = path2.split("/")[-1]

    if prefix:
        output_file = os.path.join(output_path, f"{prefix}_{model1}_{prompt1}_{date1}_{model2}_{prompt2}_{date2}.xlsx")
    else:
        output_file = os.path.join(output_path, f"{model1}_{prompt1}_{date1}_{model2}_{prompt2}_{date2}.xlsx")
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

    df_violations_merge, one_empty = _match_violations_external(information1, information2)

    return df_violations_merge, one_empty


def _get_mean_component_found(analysis_df: pd.DataFrame) -> float:
    """
    
    """
    # new column
    analysis_df["is_matched"] = analysis_df['matched_to'].notnull()

    # divide pd based on 2 columns model and prompt
    model_prompt_group = {}

    for model, prompt in zip(analysis_df["model"], analysis_df["prompt"]):
        key = (model, prompt)
        if key not in model_prompt_group:
            model_prompt_group[key] = 0
        model_prompt_group[key] += 1

    biggest_group = max(model_prompt_group.items(), key=lambda x: x[1])
    biggest_group_key = biggest_group[0]
    
    biggest_sub_df = analysis_df[
        (analysis_df['model'] == biggest_group_key[0]) & 
        (analysis_df['prompt'] == biggest_group_key[1])
    ]

    mean_score = biggest_sub_df['is_matched'].mean() if not biggest_sub_df.empty else 0.0

    grouped_df = analysis_df.groupby(['model', 'prompt', 'wcag_id', 'wcag_url']).agg(
        mean_score=('is_matched', 'mean'),
        sum_matching=('is_matched', 'sum'),
        count_entries=('unique_id', 'count')
    ).reset_index()

    grouped_df = grouped_df[(grouped_df["model"] == biggest_group_key[0]) & (grouped_df["prompt"] == biggest_group_key[1])]

    # print(grouped_df)

    return mean_score, grouped_df



def start_qualitative_analysis(info1: list, info2: list) -> pd.DataFrame:
    """
    xxx
    """
    full_df = pd.DataFrame()

    accessibility_path1, model1, prompt1 = info1
    accessibility_path2, model2, prompt2 = info2

    mean_scores = []
    grouped_violations_map = {}

    for file in os.listdir(accessibility_path1):
        if os.path.isdir(file) and not file.endswith('.json'):
            continue

        accessibility1_path_file = os.path.join(accessibility_path1, file)
        accessibility2_path_file = os.path.join(accessibility_path2, file)

        analysis_df, one_empty = create_analysis_df(
            [accessibility1_path_file, model1, prompt1],
            [accessibility2_path_file, model2, prompt2]
        )

        # print(analysis_df)
        # Interpretation
        if not one_empty:
            mean_score, violations_group_df = _get_mean_component_found(analysis_df)
            mean_scores.append(mean_score)
            
            for model_p, prompt_p, wcag_id_p, wcag_url_p in zip(violations_group_df["model"], violations_group_df["prompt"], violations_group_df["wcag_id"], violations_group_df["wcag_url"]):
                filter_df = ((violations_group_df['model'] == model_p) & 
                    (violations_group_df['prompt'] == prompt_p) & 
                    (violations_group_df['wcag_id'] == wcag_id_p) & 
                    (violations_group_df['wcag_url'] == wcag_url_p))
                
                index_entry = violations_group_df.index[filter_df].item()
                mean_score_group = violations_group_df.loc[index_entry, 'mean_score']
                sum_matching_group = violations_group_df.loc[index_entry, 'sum_matching']
                count_entries_group = violations_group_df.loc[index_entry, 'count_entries']
                
                key = (model_p, prompt_p, wcag_id_p, wcag_url_p)
                if key not in grouped_violations_map:
                    grouped_violations_map[key] = {
                        "mean_score": mean_score_group,
                        "sum_matching": sum_matching_group,
                        "count_entries": count_entries_group,
                    }
                else:
                    grouped_violations_map[key] = {
                        "sum_matching": grouped_violations_map[key].get("sum_matching") + sum_matching_group,
                        "count_entries": grouped_violations_map[key].get("count_entries") + count_entries_group,
                        "mean_score": grouped_violations_map[key].get("sum_matching") / grouped_violations_map[key].get("count_entries") if grouped_violations_map[key].get("count_entries") > 0 else 0
                    }

        # concat dataframes
        full_df = pd.concat([full_df, analysis_df], ignore_index=True)

    

    grouped_violations_df = pd.DataFrame.from_dict(
        grouped_violations_map, 
        orient='index', 
        columns=['mean_score', 'sum_matching', 'count_entries']
    ).reset_index()

    output_path = os.path.join(os.path.dirname(__file__), 'qualitative_analysis')

    _export_df_to_excel(grouped_violations_df, output_path, info1, info2, prefix="grouped_violations")

    # mean Score for all files
    if mean_scores:
        mean_score = np.mean(mean_scores)
        print(f"\n\nMean Score for all files: {mean_score}")

    _export_df_to_excel(full_df, output_path, info1, info2)

    return full_df






# Test
if __name__ == "__main__":

    data_path = os.path.join(os.path.dirname(__file__), '..')
    input_path = os.path.join(data_path, "Input")
    output_path = os.path.join(data_path, "Output")

    # Example paths
    accessibility1_path = os.path.join(input_path, 'accessibility')

    # accessibility1_naive_path = os.path.join(output_path, 'gemini', 'accessibility', 'naive', '2025-06-18-11-53')
    # accessibility1_naive_path = os.path.join(output_path, 'gemini', 'accessibility', 'naive', '2025-06-18-11-24')
    # accessibility1_naive_path = os.path.join(output_path, 'gemini', 'accessibility', 'naive', '2025-06-18-11-53')
    # accessibility1_reason_path = os.path.join(output_path, 'gemini', 'accessibility', 'reason', '2025-06-18-16-24')
    # accessibility1_reason_path = os.path.join(output_path, 'gemini', 'accessibility', 'reason', '2025-06-18-17-38')
    # accessibility1_reason_path = os.path.join(output_path, 'gemini', 'accessibility', 'reason', '2025-06-18-20-49')
    # accessibility1_zeroshot_path = os.path.join(output_path, 'gemini', 'accessibility', 'zero-shot', '2025-06-18-13-25')
    # accessibility1_zeroshot_path = os.path.join(output_path, 'gemini', 'accessibility', 'zero-shot', '2025-06-18-14-29')
    # accessibility1_zeroshot_path = os.path.join(output_path, 'gemini', 'accessibility', 'zero-shot', '2025-06-18-15-40')

    accessibility1_naive_path = os.path.join(output_path, 'openai', 'accessibility', 'naive', '2025-06-19-15-41')
    # accessibility1_naive_path = os.path.join(output_path, 'openai', 'accessibility', 'naive', '2025-06-19-16-53')
    # accessibility1_naive_path = os.path.join(output_path, 'openai', 'accessibility', 'naive', '2025-06-19-19-05')
    accessibility1_reason_path = os.path.join(output_path, 'openai', 'accessibility', 'reason', '2025-06-20-15-39')
    # accessibility1_reason_path = os.path.join(output_path, 'openai', 'accessibility', 'reason', '2025-06-20-17-42')
    # accessibility1_reason_path = os.path.join(output_path, 'openai', 'accessibility', 'reason', '2025-06-20-19-43')
    # accessibility1_zeroshot_path = os.path.join(output_path, 'openai', 'accessibility', 'zero-shot', '2025-06-20-09-55')
    # accessibility1_zeroshot_path = os.path.join(output_path, 'openai', 'accessibility', 'zero-shot', '2025-06-20-11-10')
    # accessibility1_zeroshot_path = os.path.join(output_path, 'openai', 'accessibility', 'zero-shot', '2025-06-20-12-33')

    model = "openai"  # or openai
    pack1 = [accessibility1_naive_path, model, "naive"]
    pack2 = [accessibility1_reason_path, model, "reason"]

    df_analysis = start_qualitative_analysis(pack1, pack2)


    










    