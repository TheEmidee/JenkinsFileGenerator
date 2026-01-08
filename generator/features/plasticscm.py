"""This module defines the PlasticSCM-related features and configurations for Jenkins pipelines."""

from abc import ABC
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, field_validator

from generator.core.base_feature import BaseFeature, FeatureConfig


# More documentation at https://www.jenkins.io/doc/pipeline/steps/plasticscm-plugin/

class RemoteConfig(BaseModel):
    """Configuration for remote used in PlasticSCM checkout operations."""

    repository: str = Field(description="The PlasticSCM repository name.")
    server: str = Field(description="The PlasticSCM server port.")


class CredentialsConfig(BaseModel):
    """Configuration for user remote settings in PlasticSCM checkout operations."""

    working_mode: str = Field(description="The jenkins credential id working mode. (NONE,UP,LDAP)")
    credentials_id: str = Field(description="The jenkins credentials id to use to connect to the remote.")

    @field_validator("working_mode", mode="before")
    @classmethod
    def validate_working_mode(cls, working_mode: str) -> str:
        """Ensure the workingMode is set correctly."""
        if working_mode != "NONE" and working_mode != "UP" and working_mode != "LDAP":
            raise ValueError(working_mode + " doesn't exit. Use NONE,UP or LDAP.")
        return working_mode



class PlasticSCMCheckoutConfig(BaseModel):
    """Configuration for the PlasticSCM checkout operation."""

    branch: str = Field(description="The branch name to checkout, overriden by shelveset and label.")
    changeset: Optional[str] = Field(
        default=None,
        description="The changeset to checkout, overriden by shelveset and label.",
    )
    shelveset: Optional[str] = Field(
        default=None,
        description="The shelveset to checkout, overrides branch and changeset, overriden by label.",
    )
    label: Optional[str] = Field(
        default=None,
        description="The label to checkout, overrides branch, changeset and shelveset.",
    )

    changelog: Optional[bool] = Field(
        default=True,
        description="Enable or Disable 'Include in changelog'.",
    )
    poll: Optional[bool] = Field(
        default=False,
        description="Enable or Disable 'Include in polling'.",
    )

    remote_config: RemoteConfig = Field(
        description="The remote configuration."
    )

    cleanup: Optional[str] = Field(
        default="STANDARD",
        description="Cleanup settings of the repository. (MINIMAL,STANDARD,FULL,DELETE)",
    )

    directory: Optional[str] = Field(
        default=None,
        description="The workspace subdirectory to clone the repo, required if you use multiple workspaces.",
    )

    credentials_config: Optional[CredentialsConfig] = Field(
        default=None,
        description="The crendentials configuration."
    )

    @field_validator("cleanup", mode="before")
    @classmethod
    def validate_cleanup(cls, cleanup: str) -> str:
        """Ensure the cleanup is set correctly."""
        if cleanup != "MINIMAL" and cleanup != "STANDARD" and cleanup != "FULL" and cleanup != "DELETE":
            raise ValueError(cleanup + " doesn't exit. Use MINIMAL,STANDARD,FULL or DELETE.")
        return cleanup


class PlasticSCMConfig(FeatureConfig):
    """Configuration model for the Plastic SCM properties."""

    checkout: PlasticSCMCheckoutConfig = Field(
        default=None,
        description="The checkout configuration. If use_simple_checkout is true, this will be ignored.",
    )


class PlasticSCMFeature(BaseFeature):
    """Feature for defining the Plastic SCM properties."""

    feature_name = "plasticscm"

    def should_include(self, config: Dict[str, Any]) -> bool:
        return "plasticscm" in config

    def get_config_model(self) -> BaseModel:
        return PlasticSCMConfig
