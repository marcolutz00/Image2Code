from abc import ABC, abstractmethod

class LLMStrategy(ABC):
    @abstractmethod
    def api_call(self):
        pass