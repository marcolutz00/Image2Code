import cv2
import numpy as np
from scipy.optimize import linear_sum_assignment
from pathlib import Path
from typing import List, Tuple, Sequence, Dict, Any, Optional
import sys
import os
import json
from pathlib import Path
from bs4 import BeautifulSoup
import difflib
from collections import Counter

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import Benchmarks.ocr_free_utils as ocr_free_utils
import Utils.utils_general as utils_general
import Utils.utils_dataset as utils_dataset






def _calculate_best_match(text: str, soup, min_similarity: float = 0.45) -> str:
    """
    Finds best html tag that matches text
    """
    if not text or soup is None:
        return ""

    best_tag = None
    best_similarity = 0.0

    for tag in soup.find_all(True):
        tag_txt = tag.get_text(strip=True)
        if not tag_txt:
            continue
        sim = difflib.SequenceMatcher(None, tag_txt, text).ratio()

        if sim > best_similarity:
            best_similarity, best_tag = sim, tag

    if best_tag is None or best_similarity < min_similarity:
        return ""

    html_snip = str(best_tag)
    # only short snippet part
    return html_snip[:250]


def _extract_ui_blocks(image_path: str, html_path: str,width: int, height: int):
    """
    returns ui blocks with bbox and html snippet
    """
    soup = BeautifulSoup(Path(html_path).read_text(), "html.parser")

    raw_blocks = ocr_free_utils.get_blocks_ocr_free(str(image_path), html_path)
    boxes= []
    htmls = []

    for entry in raw_blocks:
        x_norm, y_norm, w_norm, h_norm = entry["bbox"]
        x1 = int(round(x_norm * width))
        y1 = int(round(y_norm * height))
        x2 = int(round((x_norm + w_norm) * width))
        y2 = int(round((y_norm + h_norm) * height))

        temp_list = [x1, y1, x2, y2]

        boxes.append(temp_list)
        text = entry.get("text") or entry.get("innerText") or ""

        html_snippet = _calculate_best_match(text, soup)

        boxes.append(temp_list)
        htmls.append(html_snippet.strip())
    return boxes, htmls





def _find_dominant_tool(issues) -> Tuple:
    """
    just return the dominant tool (max number of issues per issue group)
    """
    issues = issues.get("issues")

    sources = [issue.get("source") for issue in issues]

    if not sources:
        return issues, "unknown"
    
    counts = Counter(sources)
    max_count = max(counts.values())

    dominant_srcs = [src for src, cnt in counts.items() if cnt == max_count]
    dominant_srcs.sort()

    dominant = dominant_srcs[0]
    filtered = [iss for iss, src in zip(issues, sources) if src == dominant]
    return filtered, dominant



def _extract_violation_items(violations):
    """
        Extracts violation item
    """

    data = violations
    data = data.get("automatic")

    violation_htmls = []

    for issue_group in data:
        filtered_issues, dominant_tool = _find_dominant_tool(issue_group)
        group_name = issue_group.get("name")

        for issue in filtered_issues:
            # If axe-core
            nodes = issue.get("nodes")
            if nodes:
                node_iter = nodes if isinstance(nodes, list) else [nodes]
                for n in node_iter:
                    html_snip = n.get("html") or n.get("snippet") or ""
                    if html_snip:
                        violation_htmls.append([group_name, html_snip.strip()])
                continue

            # If pa11y
            original_issue = issue.get("original_issue")
            if original_issue:
                context = original_issue.get("context")
                if context:
                    violation_htmls.append([group_name, context.strip()])
                continue

            # Lighthouse‑style single node
            det = issue.get("details")
            if isinstance(det, dict):
                node = det.get("node")
                if isinstance(node, dict):
                    html_snip = node.get("html") or node.get("snippet")
                    if html_snip:
                        violation_htmls.append([group_name, html_snip.strip()])

    return violation_htmls



def _calculate_similarity(a: str, b: str) -> float:
    """
        similartiy of text
    """
    if not a or not b:
        return 0.0
    
    return difflib.SequenceMatcher(None, a, b).ratio()




def extract_tag_text(html: str):
    """
        Only extracts text from html tags
    """
    soup = BeautifulSoup(html, "html.parser")

    texts = list(soup.stripped_strings)

    if not texts:
        return soup.get_text(strip=True)

    texts = [txt for txt in texts if len(txt) >= 3]

    return texts



def match_blocks_html(violation_htmls: List[str],block_htmls: List[str], threshold: float = 0.8):
    """
        Maps blocks with html
    """
    if not violation_htmls or not block_htmls:
        return {}, list(range(len(violation_htmls))), list(range(len(block_htmls))), {}
    
    distribution_violations = {
        "matched": {},
        "unmatched": {}
    }

    # similarity matrix
    sim_matrix = np.zeros((len(violation_htmls), len(block_htmls)))
    for i, violation in enumerate(violation_htmls):
        clear_text_violation = extract_tag_text(violation[1])
        for j, block in enumerate(block_htmls):
            clear_text_block = extract_tag_text(block)
            max_score = 0.0
            for text in clear_text_block:
                for text2 in clear_text_violation:
                    max_score = _calculate_similarity(text, text2) if _calculate_similarity(text, text2) > max_score else max_score
            sim_matrix[i, j] = max_score

    matches = {}
    unmatched_v = []

    # closest score (greedy)
    for i in range(len(violation_htmls)):
        best_j = int(np.argmax(sim_matrix[i]))
        best_similarity = sim_matrix[i, best_j]
        if best_similarity >= threshold:
            matches[i] = best_j
            if violation_htmls[i][0] not in distribution_violations["matched"]:
                distribution_violations["matched"][violation_htmls[i][0]] = 0
            distribution_violations["matched"][violation_htmls[i][0]] += 1
        
        else:
            unmatched_v.append(i)
            if violation_htmls[i][0] not in distribution_violations["unmatched"]:
                distribution_violations["unmatched"][violation_htmls[i][0]] = 0
            distribution_violations["unmatched"][violation_htmls[i][0]] += 1


    matched_blocks = set(matches.values())
    unmatched_b = [j for j in range(len(block_htmls)) if j not in matched_blocks]

    return matches, unmatched_v, unmatched_b, distribution_violations






def annotate_accessibility_issues(image_path: str, violations, html_path: str, similarity_threshold: float = 0.8,
) -> Dict[str, Any]:
    """
    Matching of violatinos and UI blocks in an image with stats
    """

    img = cv2.imread(str(image_path))

    h, w = img.shape[:2]

    boxes, block_htmls = _extract_ui_blocks(image_path, html_path, w, h)
    violation_htmls = _extract_violation_items(violations)

    matches, unmatched_v, unmatched_b, matched_v_dict = match_blocks_html(violation_htmls, block_htmls, threshold=similarity_threshold)


    stats = {
        "total_ui_blocks": len(boxes),
        "total_violations": len(violation_htmls),
        "matched": len(matches),
        "unmatched_violations": len(unmatched_v),
        "unmatched_ui_blocks": len(unmatched_b),
        "matched_violations_distribution": matched_v_dict,
    }

    return stats


def start_qualitative_analysis_accessibility(accessibility_path: str):
    
    """
    Start the qualitative analysis for accessibility issues.
    """

    similarity_threshold = 0.8

    image_path = accessibility_path.replace("accessibility", "images")
    html_path = accessibility_path.replace("accessibility", "html")

    general_stats = { }

    for file in utils_dataset.sorted_alphanumeric(os.listdir(accessibility_path)):
        if not file.endswith('.json') or os.path.isdir(os.path.join(accessibility_path, file)):
            continue

        violations = utils_general.read_json(os.path.join(accessibility_path, file))

        stats_file = annotate_accessibility_issues(
            image_path = os.path.join(image_path, file.replace('.json', '.png')),
            violations=violations,
            html_path=os.path.join(html_path, file.replace('.json', '.html')),
            similarity_threshold=similarity_threshold,
        )

        for key, value in stats_file.items():
            if key == "matched_violations_distribution":
                if key not in general_stats:
                    general_stats[key] = {}
                for sub_key, sub_value in value.items():
                    if sub_key not in general_stats["matched_violations_distribution"]:
                        general_stats["matched_violations_distribution"][sub_key] = {}
                    for sub_sub_key, sub_sub_value in sub_value.items():
                        if sub_sub_key not in general_stats["matched_violations_distribution"][sub_key]:
                            general_stats["matched_violations_distribution"][sub_key][sub_sub_key] = 0
                        general_stats["matched_violations_distribution"][sub_key][sub_sub_key] += sub_sub_value
                continue

            if key not in general_stats:
                general_stats[key] = 0
            general_stats[key] += value
    
    return general_stats



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

    html1_naive_path = os.path.join(output_path, 'openai', 'html', 'naive', '2025-06-19-15-41', '23.html')
    image1_naive_path = os.path.join(output_path, 'openai', 'images', 'naive', '2025-06-19-15-41', '23.png')
    accessibility1_naive_path = os.path.join(output_path, 'openai', 'accessibility', 'naive', '2025-06-19-15-41')
    # accessibility1_naive_path = os.path.join(output_path, 'openai', 'accessibility', 'naive', '2025-06-19-16-53')
    # accessibility1_naive_path = os.path.join(output_path, 'openai', 'accessibility', 'naive', '2025-06-19-19-05')
    accessibility1_reason_path = os.path.join(output_path, 'openai', 'accessibility', 'reason', '2025-06-20-15-39')
    # accessibility1_reason_path = os.path.join(output_path, 'openai', 'accessibility', 'reason', '2025-06-20-17-42')
    # accessibility1_reason_path = os.path.join(output_path, 'openai', 'accessibility', 'reason', '2025-06-20-19-43')
    # accessibility1_zeroshot_path = os.path.join(output_path, 'openai', 'accessibility', 'zero-shot', '2025-06-20-09-55')
    # accessibility1_zeroshot_path = os.path.join(output_path, 'openai', 'accessibility', 'zero-shot', '2025-06-20-11-10')
    # accessibility1_zeroshot_path = os.path.join(output_path, 'openai', 'accessibility', 'zero-shot', '2025-06-20-12-33')

    # violations = utils_general.read_json(accessibility1_naive_path)


    start_qualitative_analysis_accessibility(
        accessibility_path=accessibility1_naive_path
    )
    # annotate_accessibility_issues(image1_naive_path, violations, html1_naive_path, os.path.join(os.path.dirname(__file__), 'annotated_accessibility.png'), similarity_threshold=0.35, draw_non_violating=False)


    










    