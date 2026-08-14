from abc import ABC, abstractmethod


class EmailSender(ABC):

    @abstractmethod
    def send(self, to: str, subject: str, body: str) -> None:
        ...
