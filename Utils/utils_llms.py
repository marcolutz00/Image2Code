from pathlib import Path
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from LLMs.Strategies.openaiApiStrategy import OpenAIStrategy
from LLMs.Strategies.geminiApiStrategy import GeminiStrategy
from LLMs.Strategies.llamaLocalStrategy import LlamaStrategy
from LLMs.Strategies.qwenLocalStrategy import QwenStrategy
from LLMs.Strategies.llavaLocalStrategy import LlavaStrategy
import Utils.utils_general as util_general

def get_model_strategy(name):
    '''
        Returns strategy of the model and right parameter which can be used later
    '''
    
    match name:
        case "openai":
            strategy = OpenAIStrategy(api_key=util_general.load_keys("openai"))
            return strategy
        case "gemini":
            strategy = GeminiStrategy(api_key=util_general.load_keys("gemini"))
            return strategy
        case "llama":
            strategy = LlamaStrategy()
            return strategy
        case "qwen":
            strategy = QwenStrategy()
            return strategy
        case "llava":
            strategy = LlavaStrategy()
            return strategy
        case _:
            raise ValueError(f"Model {name} not supported.")