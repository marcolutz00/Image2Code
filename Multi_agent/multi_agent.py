import sys
import os
import json
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Multi_agent.detector_agent import DetectorAgent
from Multi_agent.identifier_agent import IdentifierAgent
from Multi_agent.resolver_agent import ResolverAgent
import Utils.utils_general as utils_general
import Utils.utils_html as utils_html
import Utils.utils_image_processing as utils_image_processing

CURR_PATH = Path(__file__).resolve().parent
DATA_PATH = CURR_PATH.parent / "Data"
INPUT_PATH = DATA_PATH / "Input"
OUTPUT_PATH = DATA_PATH / "Output"


async def run_multi_agent(client, model: str, prompt_strategy: str, code: str, image: str, date: str):
    """
        Improvement Strategy: 3-Agent Approach 
        Detector: Detects issues in code
        Identifier: identifies issues and classifies them into WCAG 2.2 guidelines
        Resolver: patches issues in code
    """
    
    base_name = os.path.splitext(image)[0]
    batch_size = 5 

    # get agents
    detector = DetectorAgent(client, model)
    identifier = IdentifierAgent(client, model)
    resolver = ResolverAgent(client, model)

    # detect issues
    issues_json, tokens_used_detector = await detector.detect_issues(code)
    
    if not issues_json:
        print("No issues found")
        return None, None, None

    # identify issues
    updated_issues_json, tokens_used_identifier = await identifier.identify_issues(code, issues_json)

    temp_code = code
    # tokens_used_resolver = 0

    # resolve issues in batches n=5
    for i in range(0, len(updated_issues_json), batch_size):
        batch = updated_issues_json[i:i + batch_size]
        print(f"Process batch {i} of {len(batch)}")
        temp_code, tokens_used_resolver_batch = await resolver.resolve_code(updated_issues_json, temp_code)
        temp_code = utils_html.clean_html_result(temp_code)
        # tokens_used_resolver += tokens_used_resolver_batch
    
    # clean final html
    resolved_code = utils_html.clean_html_result(temp_code)
    # print(f"Tokens used: {tokens_used_detector + tokens_used_identifier + tokens_used_resolver}")

    output_base_html_path, output_base_accessibility_path, output_base_images_path, output_base_insights_path = utils_general.create_directories(OUTPUT_PATH, model, f"{prompt_strategy}_agent", date)
    with open(os.path.join(output_base_html_path, f"{prompt_strategy}_agent", date, f"{base_name}.html"), "w", encoding="utf-8") as f:
        f.write(resolved_code)

    # analyze outputs
    _, accessibility_issues, accessibility_issues_overview = await utils_image_processing.analyze_outputs(image, model, f"{prompt_strategy}_agent", date)





