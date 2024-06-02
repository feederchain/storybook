import os
import requests
import subprocess
from llm_base import LLMBase

class OllamaModel(LLMBase):

    def __init__(self):
      self.OLLAMA_API = 'http://localhost:11434/api/generate'
      self.OLLAMA_MODEL = 'llama3'
      self.HOME = os.path.expanduser("~")
      self.SD_LOCATION = self.HOME + '/OnnxStream/src/build/sd'
      self.SD_MODEL_PATH = self.HOME + '/sd_models/stable-diffusion-1.5-onnxstream'
      self.SD_STEPS = 3


    def generate_text(self, persona: str, prompt: str) -> str:
      prompt = persona + prompt
      r = requests.post(self.OLLAMA_API, timeout=600,
        json = {
            'model': self.OLLAMA_MODEL,
            'prompt': prompt,
            'stream': False,
            'options': {
              'temperature': 0.9
            }
        })
      data = r.json()
      return data['response'].lstrip()
    
    
    def get_image(self, prompt: str, image_file: str):
      subprocess.run([self.SD_LOCATION, '--xl', '--turbo', '--rpi', '--models-path', self.SD_MODEL_PATH,\
                      '--prompt', prompt,\
                      '--steps', f'{self.SD_STEPS}', '--output', image_file], check=False) 
      return