from typing import Any, Dict, Optional
from pydantic import BaseModel

class ProjectConfig(BaseModel):
    name: str

class JenkinsConfig(BaseModel):
    default_node_names: str
    workspace_suffix: Optional[str] = None

class PipelineConfig(BaseModel):
    pipeline_name: str
    project: ProjectConfig
    jenkins: JenkinsConfig
    features: Dict[str, Any] = {}