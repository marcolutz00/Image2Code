from pathlib import Path
import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from LLMs.Strategies.openaiApiStrategy import OpenAIStrategy
from LLMs.Strategies.geminiApiStrategy import GeminiStrategy
from LLMs.Strategies.llamaLocalStrategy import LlamaStrategy
from LLMs.Strategies.qwenLocalStrategy import QwenStrategy
from LLMs.LLMClient import LLMClient
import Utils.utils_general as utils_general
import Utils.utils_llms as utils_llms


class DetectorAgent:
    detector_prompt = """
    You are an expert in web accessibility and HTML/CSS analysis.
    Your task is to analyze the provided HTML/CSS code below and identify accessibility issues based on the
    Web Content Accessibility Guidelines (WCAG) 2.2. 

    Analyse the following HTML/CSS.
    Return ONLY a JSON array; each element must contain:
    - line_start (int)
    - line_end   (int, inclusive)
    - snippet    (str, the code snippet that contains the issue)
    - category   (MissingAlt | LowContrast | MissingLabel | NoLandmark | ...)

    Follow the general json array format, as can be seen in the example below:
    [
        {
            "line_start": 10,
            "line_end": 10,
            "snippet": "<img src='image.png'>",
            "category": "MissingAlt"
        },
        { ... },
    ]

    Do NOT fix the code and do not add extra keys or explanations.

    Refer to the full WCAG 2.2 spec if in doubt: https://www.w3.org/TR/WCAG22/

    Let’s think step by step.
    """

    def __init__(self, client, model: str):
        self.model = model
        self.strategy = utils_llms.get_model_strategy(model)
        self.client =client

    async def detect_issues(self, code: str):
        """
            Responsible for detecting issues and return in a structured format.
            The issues are stores in a predefined list
        """
        
        issues = []
        prompt = f"{self.detector_prompt}\n\nCode:\n{code}"
        response = await self.client.agent_call(prompt)

        if response is None:
            print("No response")
            return None
        
        text, tokens_used = response

        clean_json = utils_general.clean_json_result(text)
        
        if clean_json is None or len(clean_json) == 0:
            print("Detector: No issues found")
            return issues, tokens_used
        
        for issue in clean_json:
            issue_obj = {
                "line_start": issue.get("line_start", 0),
                "line_end": issue.get("line_end", 0),
                "snippet": issue.get("snippet", ""),
                "category": issue.get("category", ""),
                "guideline": issue.get("guideline", ""),
                "severity": issue.get("severity", ""),
            }
            issues.append(issue_obj)

        return issues, tokens_used




