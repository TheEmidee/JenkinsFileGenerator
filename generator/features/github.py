from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

from ..core.base_feature import BaseFeature, FeatureConfig

class GitHubPullRequestFilterConfig(BaseModel):
    """Configuration model for pull request filter."""
    tokens: Optional[List[str]] = Field( default=None, description="List of tokens to ignore in pull requests, e.g., 'WIP', 'NO_CI'." )
    message: str = Field( description="Custom message to display when a pull request is ignored due to the filter." )

    @field_validator('tokens', mode='before')
    @classmethod
    def validate_tokens(cls, tokens: List[str]) -> List[str]:
        """Ensure tokens are not empty."""
        if not tokens:
            raise ValueError('There must be tokens in the list')
        return tokens
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, message: str) -> str:
        """Ensure the message is set."""
        if not message:
            raise ValueError('the message must be set')
        return message

class GitHubPullRequestConfig(BaseModel):
    """Configuration model for pull request utilities."""
    filter: Optional[GitHubPullRequestFilterConfig] = Field( default=None, description="Filter configuration for pull requests, e.g., tokens to ignore." )
    update_description_from_pr_body: Optional[bool] = Field( default=None, description="If true, updates the current build description with the body of the pull request." )

class GitHubConfig(FeatureConfig):
    """Configuration model for the GitHub feature."""
    credentials_id: str = Field( description="The jenkins credentials id that is associated with the GITHUB_TOKEN." )
    pull_requests: Optional[GitHubPullRequestConfig] = None

    def model_post_init(self, context):
        self._accumulator["update_job_description_from_pr"] = self.pull_requests.update_description_from_pr_body if self.pull_requests else False
        self._accumulator["can_process_pull_request"] = bool(self.pull_requests and self.pull_requests.filter)
        self._accumulator["get_github_pr_infos"] = self._accumulator["update_job_description_from_pr"] or self._accumulator["can_process_pull_request"]

class GitHubFeature(BaseFeature):
    """Feature for using GitHub."""
    
    feature_name = "github"
    
    def should_include(self, config: Dict[str, Any]) -> bool:
        return "github" in config
    
    @property
    def dependencies(self) -> List[str]:
        return ["utils"]
    
    def get_config_model(self) -> BaseModel:
        return GitHubConfig