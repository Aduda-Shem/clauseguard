from abc import ABC, abstractmethod


class ChatClient(ABC):
    @abstractmethod
    def answer(self, question: str, contract_text: str, findings_context: str, history: list[dict]) -> str:
        raise NotImplementedError
