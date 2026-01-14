"""This module defines the Git-related features and configurations for Jenkins pipelines."""

from abc import ABC
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel, Field, field_validator

from generator.core.base_feature import BaseFeature, FeatureConfig


class CredentialsIdConfig(BaseModel):
    """Configuration for credentials ID used in Git operations."""

    id: str = Field(description="The jenkins credential id to use to connect to the url.")
    url: str = Field(description="The git url to use to checkout the repository.")


class UserRemoteConfig(BaseModel):
    """Configuration for user remote settings in Git operations."""

    credentials_id: CredentialsIdConfig = Field(description="The credentials ID and URL for the remote repository.")


class GitExtensionConfig(BaseModel, ABC):
    """Base class for Git extension configurations."""

    def should_emit(self) -> bool:
        """Determine if this extension should emit text in the Jenkinsfile."""
        return True

    @classmethod
    def get_class_name(cls) -> str:
        """Class method version - returns the class name without 'Config' suffix"""
        class_name = cls.__name__
        if class_name.endswith("Config"):
            return class_name[:-6]
        return class_name


class SubmoduleOptionConfig(GitExtensionConfig):
    """Configuration for submodule options in Git operations."""

    disableSubmodules: Optional[bool] = None
    parentCredentials: Optional[bool] = None
    recursiveSubmodules: Optional[bool] = None
    reference: Optional[str] = None
    timeout: Optional[int] = None
    trackingSubmodules: Optional[bool] = None


class GitLFSPullConfig(GitExtensionConfig):
    """Configuration for Git LFS pull."""

    enabled: bool = Field(default=False, description="Set to true to pull from LFS.")

    def should_emit(self) -> bool:
        return False


class CheckoutOptionConfig(GitExtensionConfig):
    """Configuration for checkout options."""

    timeout: Optional[int] = Field(default=None, description="Timeout for the checkout operation in seconds.")


class GitCheckoutConfig(BaseModel):
    """Configuration for the Git checkout operation."""

    branch_name: str = Field(description="The branch name to checkout")
    extensions: Dict[str, GitExtensionConfig] = Field(default={}, description="The extensions to use for the checkout")
    user_remote_config: UserRemoteConfig = Field(description="The user remote configuration.")

    @field_validator("extensions", mode="before")
    @classmethod
    def validate_extensions(cls, raw_exts: Dict[str, Any]) -> Dict[str, GitExtensionConfig]:
        """Validate and parse the extensions dictionary."""
        parsed_exts: Dict[str, GitExtensionConfig] = {}
        for key, value in raw_exts.items():

            def get_config_class(yaml_key: str) -> Type[GitExtensionConfig]:
                class_name = yaml_key + "Config"
                model_cls = globals().get(class_name)
                if model_cls is None:
                    raise ValueError(f"Unknown extension key: {yaml_key}")
                return model_cls  # type: ignore[return-value,no-any-return]

            model_cls = get_config_class(key)
            if model_cls is None:
                raise ValueError(f"Unknown extension key: {key}")
            parsed_exts[key] = model_cls(**value)
        return parsed_exts


class GitConfig(FeatureConfig):
    """Configuration model for the git properties."""

    use_simple_checkout: bool = Field(
        default=True,
        description="Set to true to uses a simple `checkout scm`. Otherwise fine-tune the checkout with the other properties",
    )
    checkout: Optional[GitCheckoutConfig] = Field(
        default=None,
        description="The checkout configuration. If use_simple_checkout is true, this will be ignored.",
    )


class GitFeature(BaseFeature):
    """Feature for defining the git properties."""

    feature_name = "git"

    def should_include(self, config: Dict[str, Any]) -> bool:
        return "git" in config

    def get_config_model(self) -> Type[FeatureConfig]:
        return GitConfig
