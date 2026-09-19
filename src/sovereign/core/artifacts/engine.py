"""Interface definitions for the Artifact Engine."""

from abc import ABC, abstractmethod
from typing import List, Union

from sovereign.core.artifacts.models import ArtifactRequest, Artifact
from sovereign.core.state.models import Task, StateItem, EvidenceReference

class ArtifactRenderer(ABC):
    """Abstract renderer that formats structured state into text/json/binary."""
    
    @abstractmethod
    def render(self, task: Task, state_items: List[StateItem], evidence: List[EvidenceReference], request: ArtifactRequest) -> Union[str, bytes]:
        """Render the artifact content. Must be completely deterministic."""
        pass

class ArtifactEngine(ABC):
    """Engine responsible for consuming task state and persisting derived artifacts."""
    
    @abstractmethod
    def generate(self, request: ArtifactRequest) -> Artifact:
        """Generate, persist, and register an artifact from task state."""
        pass
