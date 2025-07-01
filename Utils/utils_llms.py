from pathlib import Path
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from LLMs.Strategies.openaiApiStrategy import OpenAIStrategy
from LLMs.Strategies.geminiApiStrategy import GeminiStrategy
from LLMs.Strategies.llamaLocalStrategy import LlamaStrategy
from LLMs.Strategies.qwenLocalStrategy import QwenStrategy
from LLMs.Strategies.hfFinetunedStrategy import HfFinetunedStrategy
from LLMs.Strategies.hfEndpointStrategy import HfEndpointStrategy
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
        case "llama_local":
            strategy = LlamaStrategy()
            return strategy
        case "llama_hf":
            endpoint_llama = None
            strategy = HfEndpointStrategy(endpoint_llama)
            return strategy
        case "qwen_local":
            strategy = QwenStrategy()
            return strategy
        case "qwen_hf":
            with open(Path(__file__).resolve().parent.parent / "keys.json", "r", encoding="utf-8") as f:
                endpoint_qwen = json.load(f)["huggingface"]["endpoint_qwen"]
            strategy = HfEndpointStrategy(endpoint_qwen)
            return strategy
        case "finetuned_hf":
            strategy = HfFinetunedStrategy()
            return strategy
        case _:
            raise ValueError(f"Model {name} not supported.")