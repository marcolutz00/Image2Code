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



class IdentifierAgent:
    identifier_prompt = """
    You are an expert in web accessibility and HTML/CSS analysis.
    Your task is to analyze the provided accessibility violations json array found by a detector agent and update this
    json array with additional information about the issues.
    For each issue, you need to classify it into an official WCAG 2.2 guideline and add its severity.
    In order to do this, you will receive the entire HTML/CSS code of the page and the accessibility issues found structured in the following format:
    [
        {
            "line_start": 10,
            "line_end": 10,
            "snippet": "<img src='image.png'>",
            "category": "MissingAlt"
        },
        { ... },
    ]   

    Your output should be a JSON array with the same structure, but with additional fields:
    [
        {
            "line_start": 10,
            "line_end": 10,
            "snippet": "<img src='image.png'>",
            "category": "MissingAlt",
            "guideline": "WCAG 2.1 – SC 1.1.1 Non-text Content (Level A)",
            "severity": "Critical" # other options: Critical, Serious, Moderate, Minor
        },
        { ... },
    ]
    Do NOT fix the code and do NOT add extra keys or explanations.
    Refer to the full WCAG 2.1 spec if in doubt: https://www.w3.org/TR/WCAG22/

    Let’s think step by step.
    """


    def __init__(self, client, model: str):
        self.model = model
        self.strategy = utils_llms.get_model_strategy(model)
        self.client = client

    async def identify_issues(self, code: str, issues = None):
        """
            Responsible for identifying / classifying issues in the code.
            Adds new fields to the issues: type, severity and description.
        """
        
        prompt = f"{self.identifier_prompt}\n\nViolations:\n{issues}\n\nCode:\n{code}"
        response = await self.client.agent_call(prompt)

        if response is None:
            print("No response")
            return None
        
        text, tokens_used = response

        clean_json = utils_general.clean_json_result(text)

        updated_issues = []

        if clean_json is None or len(clean_json) == 0:
            print("Identifier: No issues found")
            return updated_issues, tokens_used

        for issue in clean_json:
            issue_obj = {
                "line_start": issue.get("line_start", 0),
                "line_end": issue.get("line_end", 0),
                "snippet": issue.get("snippet", ""),
                "category": issue.get("category", ""),
                "guideline": issue.get("guideline", ""),
                "severity": issue.get("severity", ""),
            }
            updated_issues.append(issue_obj)

        return updated_issues, tokens_used