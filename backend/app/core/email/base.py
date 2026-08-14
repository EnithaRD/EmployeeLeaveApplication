from abc import ABC, abstractmethod


class EmailSender(ABC):
    """Contract for anything that can deliver an email. New senders (a different
    provider, a different from-account) plug in by implementing this, without
    callers changing."""

    @abstractmethod
    def send(self, to: str, subject: str, body: str) -> None:
        ...
