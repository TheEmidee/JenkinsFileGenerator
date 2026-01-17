"""Container for all generated code blocks."""

from dataclasses import dataclass, field
from typing import Dict, List

from generator.core import constants


@dataclass
class GeneratedBlocks:
    """Container for all generated code blocks."""

    blocks: Dict[str, List[str]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in constants.MAKO_BLOCKS:
            self.blocks.setdefault(key, [])

    def merge_with(self, other: "GeneratedBlocks") -> None:
        """Merge this instance with another GeneratedBlocks instance."""
        for key, value in other.blocks.items():
            if key in self.blocks:
                self.blocks[key].extend([" ", *value])
            else:
                self.blocks[key] = list(value)
