from abc import ABC, abstractmethod

class LLMBase(ABC):
    @abstractmethod
    def generate_text(self, persona: str, prompt: str) -> str:
        pass
    
    @abstractmethod
    def get_image(self, prompt: str, image_file: str):
        pass