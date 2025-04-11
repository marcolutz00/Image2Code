from abc import ABC, abstractmethod

class LLMStrategy(ABC):
    @abstractmethod
    def api_frontend_generation(self):
        pass