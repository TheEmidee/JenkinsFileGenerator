from abc import ABC
from typing import Any, Dict, Optional
from pydantic import BaseModel

class PipelineConfig(BaseModel):
    name: Optional[str] = "DefaultPipeline"
    features: Dict[str, Any] = {}