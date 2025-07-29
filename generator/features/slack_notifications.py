"""
This module defines the Slack notifications feature for Jenkins pipelines.
It includes configurations for sending notifications to Slack channels or users
The notifications can be simple text messages or rich block messages.
"""

import json

from abc import ABC
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, field_validator, model_validator

from generator.core.base_feature import BaseFeature, FeatureConfig


class SlackColor(str, Enum):
    """Predefined Slack colors for consistency."""

    GOOD = "good"
    WARNING = "warning"
    DANGER = "danger"
    BLUE = "#0000FF"

    @classmethod
    def _missing_(cls, value):
        # Allow custom hex colors
        if isinstance(value, str) and value.startswith("#"):
            return value
        return super()._missing_(value)


class SlackNotificationMessageConfig(BaseModel, ABC):
    """Base configuration for Slack notification messages."""

    enabled: Optional[bool] = Field(
        default=None, description="Whether this notification type is enabled."
    )
    color: Optional[str] = Field(
        default=None, description="Color for the notification in slack."
    )
    channel_override: str = Field(
        default="", description="Channel override for this message."
    )

    @field_validator("color", mode="before")
    @classmethod
    def convert_color_to_string(cls, v):
        """Convert SlackColor enum to string value."""
        if isinstance(v, SlackColor):
            return v.value
        return v


class SlackNotificationSimpleMessageConfig(SlackNotificationMessageConfig):
    """Configuration for simple text message notifications."""

    enabled: bool = Field(
        default=True, description="Whether to send a simple text message."
    )
    message: str = Field(default="", description="The message to send.")


class SlackNotificationBlocksMessageConfig(SlackNotificationMessageConfig):
    """Configuration for block message notifications."""

    enabled: bool = Field(
        default=False, description="Whether to send a blocks message."
    )
    blocks: str = Field(default="", description="The blocks to send.")

    @field_validator("blocks")
    @classmethod
    def validate_blocks_json(cls, v: str) -> str:
        """Ensure blocks is valid JSON."""

        try:
            json.loads(v)
        except json.JSONDecodeError as e:
            raise ValueError("blocks must be valid JSON") from e
        return v


class EventDefaults:
    """Centralized event defaults for better maintainability."""

    PRE_BUILD = {
        "message": "Build Started",
        "color": SlackColor.BLUE,
        "simple_enabled": True,
        "blocks_enabled": False,
    }

    SUCCESS = {
        "message": "Build Success",
        "color": SlackColor.GOOD,
        "simple_enabled": True,
        "blocks_enabled": False,
    }

    FAILURE = {
        "message": "Build Failed",
        "color": SlackColor.DANGER,
        "simple_enabled": True,
        "blocks_enabled": False,
    }

    UNSTABLE = {
        "message": "Build Unstable",
        "color": SlackColor.WARNING,
        "simple_enabled": True,
        "blocks_enabled": False,
    }

    EXCEPTION = {
        "message": "Build Failed. Reason ${e}",
        "color": SlackColor.DANGER,
        "simple_enabled": True,
        "blocks_enabled": False,
    }


class SlackNotificationEventConfig(BaseModel, ABC):
    """Base configuration for Slack notification events."""

    simple_message: SlackNotificationSimpleMessageConfig = Field(
        default_factory=SlackNotificationSimpleMessageConfig,
        description="Configuration for simple message notifications.",
    )
    blocks_message: SlackNotificationBlocksMessageConfig = Field(
        default_factory=SlackNotificationBlocksMessageConfig,
        description="Configuration for blocks message notifications.",
    )

    def get_defaults(self) -> Dict[str, Any]:
        """Override in subclasses to provide event-specific defaults."""
        return {}

    @model_validator(mode="after")
    def apply_defaults(self) -> "SlackNotificationEventConfig":
        """Apply defaults only to fields that weren't explicitly set."""
        defaults = self.get_defaults()
        if not defaults:
            return self

        # Apply simple message defaults
        if self.simple_message.enabled is None:
            self.simple_message.enabled = defaults.get("simple_enabled", False)
        if not self.simple_message.message and isinstance(
            self.simple_message, SlackNotificationSimpleMessageConfig
        ):
            self.simple_message.message = defaults.get("message", "")
        if self.simple_message.color is None:
            # Convert enum to string value when applying defaults
            default_color = defaults.get("color")
            self.simple_message.color = (
                default_color.value
                if isinstance(default_color, SlackColor)
                else default_color
            )

        # Apply blocks message defaults
        if self.blocks_message.enabled is None:
            self.blocks_message.enabled = defaults.get("blocks_enabled", False)
        if self.blocks_message.color is None:
            # Convert enum to string value when applying defaults
            default_color = defaults.get("color")
            self.blocks_message.color = (
                default_color.value
                if isinstance(default_color, SlackColor)
                else default_color
            )

        return self


class SlackNotificationPreBuildStepEventConfig(SlackNotificationEventConfig):
    """Pre-build step notification configuration."""

    def get_defaults(self) -> Dict[str, Any]:
        return EventDefaults.PRE_BUILD


class SlackNotificationOnSuccessEventConfig(SlackNotificationEventConfig):
    """Success event notification configuration."""

    def get_defaults(self) -> Dict[str, Any]:
        return EventDefaults.SUCCESS


class SlackNotificationOnFailureEventConfig(SlackNotificationEventConfig):
    """Failure event notification configuration."""

    def get_defaults(self) -> Dict[str, Any]:
        return EventDefaults.FAILURE


class SlackNotificationOnUnstableEventConfig(SlackNotificationEventConfig):
    """Unstable build notification configuration."""

    def get_defaults(self) -> Dict[str, Any]:
        return EventDefaults.UNSTABLE


class SlackNotificationOnExceptionEventConfig(SlackNotificationEventConfig):
    """Exception event notification configuration."""

    def get_defaults(self) -> Dict[str, Any]:
        return EventDefaults.EXCEPTION


class SlackNotificationsConfig(FeatureConfig):
    """Configuration for Slack notifications."""

    channel: str = Field(
        description="The Slack channel or user to send notifications to. Must start with # for channels or @ for users."
    )
    message_template: str = Field(
        description="Template for the message to be sent. Can include variables like env.BUILD_URL, env.JOB_NAME, etc."
    )

    # Event configurations with proper defaults
    pre_build_step: SlackNotificationPreBuildStepEventConfig = Field(
        default_factory=SlackNotificationPreBuildStepEventConfig,
        description="Configuration for the notifications sent during the pre-build step phase.",
    )
    on_success: SlackNotificationOnSuccessEventConfig = Field(
        default_factory=SlackNotificationOnSuccessEventConfig,
        description="Configuration for the notifications sent during the on-sucess step phase.",
    )
    on_failure: SlackNotificationOnFailureEventConfig = Field(
        default_factory=SlackNotificationOnFailureEventConfig,
        description="Configuration for the notifications sent during the on-failure step phase.",
    )
    on_unstable: SlackNotificationOnUnstableEventConfig = Field(
        default_factory=SlackNotificationOnUnstableEventConfig,
        description="Configuration for the notifications sent during the on-unstable step phase.",
    )
    on_exception: SlackNotificationOnExceptionEventConfig = Field(
        default_factory=SlackNotificationOnExceptionEventConfig,
        description="Configuration for the notifications sent during the on-exception step phase.",
    )

    webhook_credential_id: Optional[str] = Field(
        default=None, description="The Jenkins credentials ID for the Slack webhook."
    )

    @field_validator("channel")
    @classmethod
    def validate_channel(cls, v):
        """Validate channel name format."""
        if not v:
            raise ValueError("Channel cannot be empty")
        if not (v.startswith("#") or v.startswith("@")):
            raise ValueError(
                "Channel must start with # (for channels) or @ (for users)"
            )
        return v

    @model_validator(mode="after")
    def validate_configuration(self) -> "SlackNotificationsConfig":
        """Validate overall configuration consistency."""
        # Ensure at least one notification type is enabled across all events
        events = [
            self.pre_build_step,
            self.on_success,
            self.on_failure,
            self.on_unstable,
            self.on_exception,
        ]

        has_enabled_notification = any(
            event.simple_message.enabled or event.blocks_message.enabled
            for event in events
        )

        if not has_enabled_notification:
            raise ValueError("At least one notification must be enabled")

        return self

    def model_post_init(self, __context):
        """Post-initialization to set up accumulator values."""
        self._accumulator["generate_send_message"] = any(
            event.simple_message.enabled
            for event in [
                self.pre_build_step,
                self.on_success,
                self.on_failure,
                self.on_unstable,
                self.on_exception,
            ]
        )
        self._accumulator["generate_send_blocks"] = any(
            event.blocks_message.enabled
            for event in [
                self.pre_build_step,
                self.on_success,
                self.on_failure,
                self.on_unstable,
                self.on_exception,
            ]
        )


class SlackNotificationsFeature(BaseFeature):
    """Feature for adding Slack notifications to Jenkins pipelines."""

    feature_name = "slack_notifications"

    def should_include(self, config: Dict[str, Any]) -> bool:
        """Determine if this feature should be included based on configuration."""
        slack_config = config.get("slack_notifications")
        if not slack_config:
            return False

        return bool(slack_config.get("channel"))

    def get_config_model(self) -> BaseModel:
        return SlackNotificationsConfig
