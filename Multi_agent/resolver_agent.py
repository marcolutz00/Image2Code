from pathlib import Path
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from LLMs.Strategies.openaiApiStrategy import OpenAIStrategy
from LLMs.Strategies.geminiApiStrategy import GeminiStrategy
from LLMs.Strategies.llamaLocalStrategy import LlamaStrategy
from LLMs.Strategies.qwenLocalStrategy import QwenStrategy
from LLMs.LLMClient import LLMClient
import Utils.utils_general as utils_general
import Utils.utils_html as utils_html
import Utils.utils_llms as utils_llms


class ResolverAgent:
    resolver_prompt = """
    You are an expert in web accessibility and HTML/CSS analysis.
    Your task is to analyze the provided accessibility violations (json array structure) found by a detector agent and patch 
    the issues in the HTML/CSS code below.
    You will receive the entire HTML/CSS code of the page and the accessibility issues found structured in the following format, 
    as you can see in the example below:
    [
        {
            "line_start": 10,
            "line_end": 10,
            "snippet": "<img src='image.png'>",
            "category": "MissingAlt",
            "guideline": "WCAG 2.2 – SC 1.1.1 Non-text Content (Level A)",
            "severity": "Critical"
        },
        { ... },
    ]

    Your output should be the fixed HTML/CSS code, with the issues patched.
    Do NOT fix other parts of the code apart from the issues specified and do NOT add extra keys or explanations.
    Refer to the full WCAG 2.2 spec if in doubt: https://www.w3.org/TR/WCAG22/

    Let’s think step by step.
    """

    def __init__(self, client, model: str):
        self.model = model
        self.strategy = utils_llms.get_model_strategy(model)
        self.client= client

    async def resolve_code(self, issues, code: str = None):
        """
            Responsible for patching issues in the code.
        """
        
        prompt = f"{self.resolver_prompt}\n\n{issues}\n\n{code}"
        response = await self.client.agent_call(prompt)

        if response is None:
            print("Agent Resolver: No response")
            return None
        
        text, tokens_used = response

        clean_html = utils_html.clean_html_result(text)

        return clean_html, tokens_used