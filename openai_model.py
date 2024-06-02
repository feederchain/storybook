import os
import requests
from openai import OpenAI
from llm_base import LLMBase

class OpenAIModel(LLMBase):
    
    def __init__(self, api_key: str):
        os.environ["OPENAI_API_KEY"] = api_key
        self.client = OpenAI()
        self.llm_model = "gpt-4o"
        self.image_model = "dall-e-3"
        

    def generate_text(self, persona: str, prompt: str) -> str:
        response = self.client.chat.completions.create(
          model=self.llm_model,
          messages=[
            {"role": "system", "content": persona},
            {"role": "user", "content": prompt}
          ]
        )
        return response.choices[0].message.content
    
    
    def get_image(self, prompt: str, image_file: str):
        response = self.client.images.generate(
          model=self.image_model,
          prompt=prompt,
          size="1024x1024",
          quality="standard",
          n=1,
        )

        image_url = response.data[0].url
        
        img_response = requests.get(image_url)
        if img_response.status_code == 200:
            with open(image_file, 'wb') as file:
                file.write(img_response.content)
        else:
            raise Exception(f"Failed to download image. Status code: {img_response.status_code}")
