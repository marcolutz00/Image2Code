from abc import ABC, abstractmethod

class LLMStrategy(ABC):
    @abstractmethod
    def llm_frontend_generation(self):
        pass

    @abstractmethod
    def llm_frontend_refinement(self):
        pass