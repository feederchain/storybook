import requests
import replicate
from llm_base import LLMBase


class ReplicateModel(LLMBase):
    
    def __init__(self, api_key: str):
        self.client = replicate.Client(api_key)
        self.llm_model = "meta/meta-llama-3.1-405b-instruct"
        self.image_model = "black-forest-labs/flux-pro"
        
        
    def generate_text(self, persona: str, prompt: str) -> str:
        
        text_template = {
            "max_tokens": 1024,
            "min_tokens": 0,
            "temperature": 2.0,
            "system_prompt": persona
        }
        
        text_template["prompt"] = prompt
        
        output = self.client.run(self.llm_model, input=text_template)

        response = ''
        if isinstance(output, list):
            response = ''.join(output)
        
        return response
    
    
    def get_image(self, prompt: str, image_file: str):
        
        image_template = {
            "num_outputs": 1,
            "aspect_ratio": "1:1",
            "output_format": "png",
            "safety_tolerance": 5,
            "output_quality": 100
        }
        
        image_template["prompt"] = prompt
        
        output = self.client.run(self.image_model, input=image_template)
        
        image_url = ""
        if isinstance(output, list):
            image_url = output[0]
        else:
            image_url = output
        
        img_response = requests.get(image_url)
        if img_response.status_code == 200:
            with open(image_file, 'wb') as file:
                file.write(img_response.content)
        else:
            raise Exception(f"Failed to download image. Status code: {img_response.status_code}")