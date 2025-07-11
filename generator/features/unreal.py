import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from pathlib import Path

from .. import logger
from ..core.base_feature import BaseFeature, FeatureConfig
from ..core.template_context import TemplateContext
from ..utils import call_external_module

class UnrealBuildGraphPostTasksConfig(BaseModel):
    """Configuration for post tasks in Unreal Build Graph."""
    enabled: bool = True
    archive_artifacts: Optional[bool] = True

class UnrealBuildGraphConfig(BaseModel):
    target: str
    node_name_filters: Optional[Dict[str, str]] = None
    properties: Optional[Dict[str,str]] = None
    post_tasks: Optional[UnrealBuildGraphPostTasksConfig] = UnrealBuildGraphPostTasksConfig()

class UnrealCleanupConfig(BaseModel):
    enabled: Optional[bool] = None
    additional_node_name : Optional[str] = None

class UnrealProjectConfig(BaseModel):
    """Configuration model for the project section of Unreal."""
    uproject_path: Path
    pyscripts_folder: Path = Field(default_factory=lambda: None) # Done like this to make it optional in the config file but will try to be set to a relative path from the uproject_path

    @field_validator('uproject_path')
    @classmethod
    def validate_uproject_path(cls, uproject_path : Path) -> Path:
        """Validate the uproject file exists."""
        if not uproject_path.is_absolute():
            logger.debug(f"uproject_path is a relative path, resolving against the current file's directory")

            this_file_folder_path = Path(__file__).parent
            uproject_path = (this_file_folder_path / "../../" / uproject_path).absolute()

        if not uproject_path.is_file():
            raise ValueError('uproject_path does not point to a valid file')
        
        logger.info(f"Resolved uproject_path: {uproject_path}")

        return uproject_path
    
    @model_validator(mode='after')
    def validate_model(self) -> 'UnrealProjectConfig':
        """Validate the location of the UEPyscripts package."""
        if self.pyscripts_folder is None:
            logger.debug(f"pyscripts_folder is not set. Default to PyScripts")
            self.pyscripts_folder = Path("PyScripts")

        if not self.pyscripts_folder.is_absolute():
            uproject_path = self.uproject_path
            if uproject_path is None:
                raise ValueError("uproject_path must be validated before pyscripts_folder")

            logger.debug(f"pyscripts_path is a relative path, resolving against the uproject located at {uproject_path}")

            self.pyscripts_folder = uproject_path.parent / self.pyscripts_folder

        if not self.pyscripts_folder.is_dir():
            raise ValueError(f"Pyscripts folder not found at {self.pyscripts_folder}.")

        logger.info(f"Resolved pyscripts_folder: {self.pyscripts_folder}")
        return self

class UnrealConfig(FeatureConfig):
    """Configuration model for the unreal feature."""

    project: UnrealProjectConfig
    buildgraph: UnrealBuildGraphConfig
    cleanup_after_build : Optional[UnrealCleanupConfig] = None

class UnrealFeature(BaseFeature):
    """Feature for using Unreal Engine."""
    
    feature_name = "unreal"
    
    def should_include(self, config: Dict[str, Any]) -> bool:
        return "unreal" in config
    
    def get_config_model(self) -> BaseModel:
        return UnrealConfig
    
    @property
    def dependencies(self) -> List[str]:
        return ["utils"]
    
    def render_block(self, block_type: str, context: TemplateContext, template) -> str:
        if block_type == "build_steps":
            jenkins_jobs = self.get_jenkins_jobs(context.feature_config)
            context.feature_config._accumulator["jenkins_jobs_output"] = jenkins_jobs

        return super().render_block(block_type, context, template)
    
    def get_jenkins_jobs(self, config: UnrealConfig) -> str:
        """Generate the Jenkins jobs for Unreal."""
        module_path = config.project.pyscripts_folder
        module_name = "uepyscripts.ci.jenkins.generate_jenkins_jobs"


        arguments = ['--target', config.buildgraph.target, '--properties', json.dumps(config.buildgraph.properties)]
        output, result = call_external_module(module_path, module_name, arguments)
        return output
    
    