from dataclasses import dataclass, field
from typing import Dict, List

@dataclass
class GeneratedBlocks:
    """Container for all generated code blocks."""
    blocks: Dict[str,List[str]] = field(default_factory=dict)

    def merge_with(self, other: 'GeneratedBlocks'):
        """Merge this instance with another GeneratedBlocks instance."""
        for key, value in other.blocks.items():
            if key in self.blocks:
                self.blocks[key].extend(value)
            else:
                self.blocks[key] = list(value)

def make_generated_blocks() -> GeneratedBlocks:
    blocks = GeneratedBlocks()
    blocks.blocks["libraries"] = []
    blocks.blocks["imports"] = []
    blocks.blocks["properties"] = []
    blocks.blocks["pre_pipeline_steps"] = []
    blocks.blocks["pre_build_steps"] = []
    blocks.blocks["on_build_unstable"] = []
    blocks.blocks["on_build_failure"] = []
    blocks.blocks["on_build_success"] = []
    blocks.blocks["post_build_steps"] = []
    blocks.blocks["on_exception_thrown"] = []
    blocks.blocks["on_finally"] = []
    blocks.blocks["additional_functions"] = []
    return blocks