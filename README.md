# First Steps
1. Install the requirements: `pip install -r requirements.txt`
2. Add the API-Keys to `keys.json`

# Files
### /practical:
- **`keys.json`**: Contains the API-Keys for the different LLMs & ImgBB. Format: 
    "openai": {
      "api_key": "..."
    },
    "claude": {
      "api_key": "..."
    },
- **`pipeline.py`**: Contains the Pipeline class which is responsible for the whole process of Image2Code.

#### /practical/API
- **`apiCalls.py`**: Contains LLM-Client class which allows to use different LLMs (Strategies).

##### /practical/API/Strategies
- **`LLMStrategy.py`**: Abstract Base-Class `LLMStrategy` for different API-Strategies.

#### /practical/Data:
- Input (Images) and Output (Code) of the LLM-Client.

#### /practical/Utils
- Util functions for the Pipeline.


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
