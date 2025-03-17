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

# Files
### /practical:
- **`keys.json`**: Contains the API-Keys for the different LLMs & ImgBB.
- **`pipeline.py`**: Contains the Pipeline class which is responsible for the whole process of Image2Code.
- **`preparation.py`**: Script to prepare necessary data, particularly downloading and storing datasets from HuggingFace.

#### /practical/API
- **`apiCalls.py`**: Contains LLM-Client class which allows to use different LLMs (Strategies).

##### /practical/API/Strategies
- **`LLMStrategy.py`**: Abstract Base-Class `LLMStrategy` for different API-Strategies.

#### /practical/ImageUpload:
- **`imageUploader.py`**: Class for uploading images to ImgBB

#### /practical/Data:
- Input and Output of the LLM-Client.

#### /practical/Utils
- **`utils.py`**: Util functions for the Pipeline (e.g. loading API keys, saving generated code, validating HTML, and creating screenshots.)
- **`tokenCounter.py`**: Token Counter for the generated code.
- **`htmlAnalyzer.py`**: nalyzing HTML, including DOM extraction, bounding box calculation and accessibility analysis.
- **`huggingFace.py`**: Functions for interacting with HuggingFace datasets

#### /practical/Benchmarks
tbd




### /theoretical:
- Space for the theoretical, written part of the thesis.



# Background Information
## Possible similarity scores:
- Structural Similary Index (SSIM): visual similarity
- TreeBLEU - measures the match of the DOM tree structure
- ClipScore

## Accessability
- WCAG
- Tools: AChecker, WAVE
