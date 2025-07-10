from dataclasses import dataclass, field
from typing import Dict, List

@dataclass
class GeneratedBlocks:
    """Container for all generated code blocks."""
    blocks: Dict[str,List[str]] = field(default_factory=dict)

    def __post_init__(self):
        required_keys = [
            "libraries",
            "imports",
            "properties",
            "pre_pipeline_steps",
            "build_steps",
            "on_build_unstable",
            "on_build_failure",
            "on_build_success",
            "post_build_steps",
            "on_exception_thrown",
            "on_finally",
            "additional_functions",
        ]
        for key in required_keys:
            self.blocks.setdefault(key, [])

    def merge_with(self, other: 'GeneratedBlocks'):
        """Merge this instance with another GeneratedBlocks instance."""
        for key, value in other.blocks.items():
            if key in self.blocks:
                self.blocks[key].extend(value)
            else:
                self.blocks[key] = list(value)