from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class TemplateContext:
    """Rich context passed to template rendering functions."""
    full_config: Dict[str, Any]
    feature_config: Dict[str, Any]
    global_values: Dict[str, Any]