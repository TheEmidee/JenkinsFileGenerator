from abc import ABC
from typing import Any, Dict, Optional
from pydantic import BaseModel, field_validator, model_validator

from ..core.base_feature import BaseFeature, FeatureConfig

class CredentialsIdConfig(BaseModel):
    id: str
    url: str

class UserRemoteConfig(BaseModel):
    credentials_id: CredentialsIdConfig

class GitExtension(BaseModel,ABC):
    def should_emit(self):
        return True
    
    @classmethod
    def get_class_name(cls):
        """Class method version - returns the class name without 'Config' suffix"""
        class_name = cls.__name__
        if class_name.endswith('Config'):
            return class_name[:-6]
        return class_name

class SubmoduleOptionConfig(GitExtension):
    disableSubmodules: Optional[bool] = None
    parentCredentials: Optional[bool] = None
    recursiveSubmodules: Optional[bool] = None
    reference: Optional[str] = None
    timeout: Optional[int] = None
    trackingSubmodules: Optional[bool] = None

class GitLFSPullConfig(GitExtension):
    enabled: bool = False

    def should_emit(self):
        return False

class CheckoutOptionConfig(GitExtension):
    timeout: Optional[int] = None

def get_config_class_name(yaml_key : str) -> str:
    return globals()[ yaml_key + "Config" ]

class GitConfig(FeatureConfig):
    """Configuration model for the git properties."""
    use_simple_checkout : bool = True
    branch_name: Optional[str] = None
    extensions: Dict[str, GitExtension]
    user_remote_config: Optional[UserRemoteConfig] = None

    @model_validator(mode='before')
    @classmethod
    def validate_configuration(cls, values):
        if isinstance(values, dict):
            use_simple_checkout = values.get('use_simple_checkout')
            
            if use_simple_checkout is False:
                # When use_simple_checkout is False, we need the full configuration
                if not values.get('branch_name'):
                    raise ValueError('branch_name is required when use_simple_checkout is False')
                if not values.get('user_remote_config'):
                    raise ValueError('user_remote_config is required when use_simple_checkout is False')
        
        return values
    
    @field_validator("extensions", mode="before")
    @classmethod
    def validate_extensions(cls, raw_exts: Dict[str, Any]) -> Dict[str, GitExtension]:
        parsed_exts = {}
        for key, value in raw_exts.items():
            model_cls = get_config_class_name(key)
            if model_cls is None:
                raise ValueError(f"Unknown extension key: {key}")
            parsed_exts[key] = model_cls(**value)
        return parsed_exts

class GitFeature(BaseFeature):
    """Feature for defining the git properties."""

    feature_name = "git"
    
    def should_include(self, config: Dict[str, Any]) -> bool:
        return "git" in config
    
    def get_config_model(self) -> BaseModel:
        return GitConfig