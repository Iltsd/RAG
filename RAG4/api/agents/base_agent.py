# api/agents/base_agent.py
from abc import ABC, abstractmethod
import logging

class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"agent.{name}")
    
    @abstractmethod
    def process(self, data):
        """Основной метод обработки данных"""
        pass
    
    def log(self, message: str):
        print(f"[{self.name}] {message}")