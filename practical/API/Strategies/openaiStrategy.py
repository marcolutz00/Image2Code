import LLMStrategy
import openai

class OpenAIStrategy(LLMStrategy):
    def __init__(self, api_key):
        self.api_key = api_key

    def api_call(self, prompt, image_path):

        # Read UI-Screenshots
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()

        # ToDo: Prompt-Engineering 
        prompt = "Please convert the following image into HTML/CSS."

        response = openai.ChatCompletion.create(
            model="gpt-4-vision-preview",
            messages=[
                {"role": "system", "content": f"{prompt}"},
                {"role": "user", "content": prompt},
                {"role": "user", "content": "Hier ist das Bild:", "image": image_data}
            ]
        )
        return response["choices"][0]["message"]["content"]