from abc import ABC, abstractmethod

class BaseConnector(ABC):

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def execute_query(self, query: str):
        pass

    @abstractmethod
    def close(self):
        pass

