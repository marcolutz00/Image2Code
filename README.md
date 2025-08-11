# First Steps

1. Install the requirements: `pip install -r requirements.txt`
2. Add the API-Keys to `keys.json` (Necessary for LLMs, ImgBB, HuggingFace)

```json
{
  "openai": {
    "api_key": "your-openai-key"
  },
  "imgbb": {
    "api_key": "your-imgbb-key"
  },
  "huggingface": {
    "api_key": "your-huggingface-key"
  }
}
```

## File Overview

### Root directory
- `README.md` – Project overview, setup, and folder structure.
- `requirements.txt` – Python dependencies for `pip install -r requirements.txt`.
- `keys.json` – API keys for OpenAI, Gemini and eventually Hugging Face.
- `pipeline.py` – Central pipeline class; orchestrates the image-to-code process (load inputs, call models, save results).

### Accessibility
- `Accessibility/mappingCsAndAxeCore.json` – Mapping between accessibility standards/tools (e.g., WCAG ↔ axe-core).
- `Accessibility/accessibilityMapping.py` – Evaluates and aggregates WCAG mapping.
- `Accessibility/accessibilityIssues.py` – Runs automated accessibility checks on generated HTML.
- `Accessibility/color_recommendation.py` – Returns Color Recommendations, necessary for Color-Aware prompt.

### Benchmarks
- `Benchmarks/accessibilityBenchmarks.py` – Scores accessibility based on defined metrics.
- other files: Visual Similarity based on Design2Code (https://github.com/NoviScl/Design2Code)

### Data
- `Data/Analysis` – Quantitative and Qualitative Analysis of generated code.
- `Data/Input` – Human Input / Benchmark Dataset
- `Data/Output` – Output of MLLMs

### Data_leakage_test
- `Data_leakage_test/Data` – Synthetic Dataset to rule out data leakage.
- `Data_leakage_test/Results` – Results of data leakage tests.

### LLMs
- `LLMs/LLMClient.py` – Client for interacting with LLMs.
- `LLMs/Strategies` – Various strategies for interacting with different LLMs. (Strategy Design Pattern)

### Multi_agent
- `Multi_agent/detector_agent.py` – According to agentic prompting -> Detector
- `Multi_agent/identifier_agent.py` – According to agentic prompting -> Identifier
- `Multi_agent/resolver_agent.py` – According to agentic prompting -> Resolver
- `Multi_agent/multi_agent.py` – Multi-Agent orchestration and management.

### Results
- `Results/accessibility` - Results for accessibility of each model per run (also average results) 
- `Results/benchmarks` - Results for benchmarks of each model per run (also average results)
- `Results/human_code` - Results for human code evaluation -> Input

### Utils
Necessary Utils for the project. They combine different functionalities, e.g.,:
- Contains prompts
- Contains necessary functionalities for ReAct prompt (here iterative)
- Image-Processing functionalities
