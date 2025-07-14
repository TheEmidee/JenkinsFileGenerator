import importlib
import json
import os
import sys
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from pathlib import Path
from mako.template import Template

from .. import logger
from ..core.base_feature import BaseFeature, FeatureConfig
from ..core.template_context import TemplateContext
from ..utils.graph import Graph

class UnrealBuildGraphPostTasksConfig(BaseModel):
    """Configuration for post tasks in Unreal Build Graph."""
    enabled: bool = True
    archive_artifacts: Optional[bool] = True

class UnrealBuildGraphConfig(BaseModel):
    target: str
    node_name_filters: Optional[Dict[str, str]] = None
    properties: Optional[Dict[str,str]] = None
    pre_tasks: Optional[List[str]] = None
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
        module_name = "uepyscripts.run.buildgraph"

        abs_package_root = os.path.abspath(module_path)
        if abs_package_root not in sys.path:
            sys.path.insert(0, abs_package_root)

        uepyscripts = importlib.import_module(module_name)
        
        temp_folder = uepyscripts.project.project_folders.saved_folders.temp
        temp_folder.mkdir(parents=True, exist_ok=True)

        export_path = temp_folder.joinpath("buildgraph.json")

        extra_parameters = [
            f"-Export={export_path}",
            "uebp_UATMutexNoWait=1"
        ]

        output_folder = uepyscripts.project.root_folder.joinpath(uepyscripts.config["Jenkins"]["OutputFolder"])
        logger.info(f"Output folder : {output_folder}")
        if not output_folder.exists():
            raise Exception("The folder where to output the jenkinsfile does not exist")

        uepyscripts.run( config.buildgraph.target, config.buildgraph.properties, extra_parameters )

        def read_json(path : Path) -> str:
            with open(path) as f:
                return json.load(f)
        
        json_contents = read_json(export_path)

        class BuildNode:
            def __init__(
                self,
                json_node
            ):
                self.name = json_node['Name']
                self.depends_on : list[str] = []
                
                depends_on = json_node['DependsOn']
                if depends_on:
                    self.depends_on = depends_on.split(';')

        class BuildGroup:
            def __init__(
                self,
                json_node
            ):
                self.name = json_node['Name']
                self.nodes = []
                for node in json_node['Nodes']:
                    self.nodes.append(BuildNode(node))

        class BuildPlatform:
            def __init__(
                self,
                name : str
            ):
                self.name = name
                self.job_to_group : dict[str,str] = {}
                self.groups : dict[str,BuildGroup] = {}
                self.parallel_groups : list[list[str]] = []

            def parse_group(self,json_node):
                group = BuildGroup(json_node)
                self.groups.update( { group.name : group } )

                for node in group.nodes:
                    self.job_to_group.update( { node.name : group.name } )

            def build_parallel_groups(self):
                g = Graph()

                for group_name, group in self.groups.items():
                    for node in group.nodes:
                        for dependency in node.depends_on:
                            required_group_name = self.job_to_group[dependency]
                            if required_group_name != group.name:
                                g.add_edge(group.name,required_group_name)

                self.parallel_groups = g.topological_sort_with_hierarchy()

        class BuildContext:
            def __init__(
                self,
                json,
                buildgraph_properties : dict[str,str] = None 
            ):
                self.inlined_properties : str = ""
                self.platforms : dict[str,BuildPlatform] = {}

                if buildgraph_properties is not None:
                    for key, value in buildgraph_properties.items():
                        self.inlined_properties += f"-set:{key}={value} "

                for group in json['Groups']:
                    platform_name = group['Agent Types'][0]
                    
                    build_platform : BuildPlatform = None
                    if platform_name not in self.platforms:
                        build_platform = BuildPlatform(platform_name)
                        self.platforms[platform_name] = build_platform
                    else:
                        build_platform = self.platforms[platform_name]

                    build_platform.parse_group(group)

                for name, platform in self.platforms.items():
                    platform.build_parallel_groups()

        TEMPLATE = """
            def buildgraph_properties = "${ctx.inlined_properties}"

            def buildgraph_job_groups = [
        % for platform_name,platform in ctx.platforms.items():
            % for group_names in platform.parallel_groups:
                [
                % for group_name in group_names:
                    [
                        "${group_name}": [
                            tasks: [ ${", ".join(f'"{node.name}"' for node in platform.groups[group_name].nodes)} ],
                            platform: "${platform_name}"
                        ],
                    ],
                % endfor
                ],
            % endfor
        % endfor
            ]

            buildgraph_job_groups.each { group ->
                executeJobsInParallel(group, buildgraph_properties)
            }
        """


        build_context = BuildContext(json_contents,config.buildgraph.properties)

        jobs_template = Template(TEMPLATE)
        return jobs_template.render(ctx=build_context)