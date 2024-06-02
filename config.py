import json
from ollama_model import OllamaModel
#from openai_model import OpenAIModel

def load_config(config_file: str):
    with open(config_file, 'r') as file:
        config = json.load(file)
    return config

def get_llm(config):
    if config['llm_provider'] == 'ollama':
        return OllamaModel()
    #elif config['llm_provider'] == 'openai':
    #    return OpenAIModel(config['openai_api_key'])
    else:
        raise ValueError("Unsupported LLM provider")
