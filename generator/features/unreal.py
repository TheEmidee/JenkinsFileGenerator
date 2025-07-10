from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from ..core.base_feature import BaseFeature

class UnrealCleanupConfig(BaseModel):
    enabled: Optional[bool] = None
    additional_node_name : Optional[str] = None

class UnrealConfig(BaseModel):
    """Configuration model for the unreal feature."""
    cleanup_after_build : Optional[UnrealCleanupConfig] = None

class UnrealFeature(BaseFeature):
    """Feature for using Unreal Engine."""
    
    feature_name = "unreal"
    
    def should_include(self, config: Dict[str, Any]) -> bool:
        return "unreal" in config
    
    def get_config_model(self) -> BaseModel:
        return UnrealConfig