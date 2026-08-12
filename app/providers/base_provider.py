from abc import ABC,abstractmethod
class BaseProvider(ABC):
    @abstractmethod 
    def generate(self,prompt:str)->str:
        pass
