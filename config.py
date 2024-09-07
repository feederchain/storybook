import json
from ollama_model import OllamaModel
from openai_model import OpenAIModel
from replicate_model import ReplicateModel

def load_config(config_file: str):
    with open(config_file, 'r') as file:
        config = json.load(file)
    return config


def load_api_keys(api_keys_file: str):
    with open(api_keys_file, 'r') as file:
        api_keys = json.load(file)
    return api_keys


def get_llm(config, api_keys):
    if config['llm_provider'] == 'ollama':
        return OllamaModel()
    elif config['llm_provider'] == 'openai':
        return OpenAIModel(api_keys['openai_api_key'])
    elif config['llm_provider'] == 'replicate':
        return ReplicateModel(api_keys['replicate_api_key'])
    else:
        raise ValueError("Unsupported LLM provider")
