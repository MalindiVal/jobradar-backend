from abc import ABC, abstractmethod

class BaseJobConnector(ABC):
    name: str

    @abstractmethod
    async def search_jobs(self, criteria: dict) -> list[dict]:
        raise NotImplementedError
