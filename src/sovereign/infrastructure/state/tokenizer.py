"""Token counting abstraction."""

from abc import ABC, abstractmethod

class TokenCounter(ABC):
    """Abstract tokenizer interface."""
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        pass

class ApproximateTokenCounter(TokenCounter):
    """
    Deterministic approximate local token estimator.
    Exact model-compatible tokenization will be integrated when the 
    model tokenizer is made available locally.
    """
    
    def count_tokens(self, text: str) -> int:
        # A standard heuristic: 1 token ~= 4 characters in English
        return max(1, len(text) // 4)
