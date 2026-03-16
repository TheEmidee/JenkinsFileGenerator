"""This feature works by using Buildgraph in an Unreal Engine project.
It requires that you use
* UEProjectBootStrap : https://github.com/TheEmidee/UEProjectBootstrap
* PyScripts https://github.com/TheEmidee/UEPyScripts

In a nutshell, this is how this feature works:
1. Before generating any text to output in the Jenkinsfile, this feature will run the
module `uepyscripts.run.buildgraph` by passing the buildgraph.target and buildgraph.properties,
as well as the `Export` parameter. This will generate a JSON file that will contain all the tasks that need to be executed.
2. We then read the JSON file and create a graph of tasks.
3. We use a topological sorting algorithm to group the tasks that can be executed in parallel, respecting the dependencies.
4. Finally, we output in the jenkinsfile an array of those tasks, and the associated functions to execute those tasks in parallel.

And this is how the tasks are executed by Jenkins:
1. Each group of tasks is passed to the generated additional function `executeJobsInParallel`,
which will call the function `runBuildGraph` for each task.
2. This function uses the module `uepyscripts.tools.ci.buildgraph` from PyScripts.
This module is a wrapper around the regular uepyscripts.run.buildgraph module.
3. This module will execute BuildGraph with the target and properties, as expected, but will pass 4 extra arguments:
* -BuildMachine
* -SharedStorageDir="\\\\path\\to\\shared\\dir'
* -WriteToSharedStorage,
* -SingleNode="task_name"
Those arguments will make buildgraph execute only the task specified by the `SingleNode` argument,
and will write the results to the shared storage directory.
4. If later down the pipeline a task needs to read the results of a previous task,
it will read them from the shared storage directory.
5. When jenkins is done, the shared storage directory is cleaned up at the end of the pipeline to avoid cluttering
the disk with old results, and to make sure that there are no artifacts left from previous jobs.

Note that the script Setup.ps1 created by UEProjectBoostrap will be called when needed before any unreal task is executed
to ensure that all the requirements (such as Python and the required moduldes) are installed on the machine.
"""

import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, cast

from mako.template import Template  # type: ignore[import-untyped]
from pydantic import BaseModel, Field, ValidationInfo, field_validator, model_validator

from generator import logger
from generator.core.base_feature import BaseFeature, FeatureConfig
from generator.core.template_context import TemplateContext
from generator.utils.graph import Graph


class UnrealBuildGraphConfig(BaseModel):
    """Configuration for Unreal Build Graph tasks."""

    target: str = Field(description="The target to build with Build Graph.")
    node_name_filters: Optional[Dict[str, str]] = Field(
        default=None,
        description=(
            "Filters to apply to the node names. Keys are the buildgraph task names and values are the jenkins node filter."
            "(Ex: `'MyGame Editor Win64 Test=BootTest': '!NoGPU'` will not select machine with no GPU to run the BootTest)"
        ),
    )
    properties: Optional[Dict[str, str]] = Field(
        default=None,
        description="Properties to pass to build graph. These are passed as -set:PropertyName=PropertyValue arguments.",
    )
    pre_tasks: Optional[List[str]] = Field(
        default=None,
        description="List of tasks to run before the buildgraph tasks.",
    )


class UnrealCleanupConfig(BaseModel):
    """Configuration for cleanup tasks after the buildgraph tasks."""

    enabled: Optional[bool] = Field(
        default=True,
        description="If true, runs the cleanup tasks after the buildgraph.",
    )
    additional_node_name: Optional[str] = Field(
        default=None,
        description="Additional node tags to use if you want the cleanup tasks to be executed on specific nodes.",
    )


class UnrealProjectConfig(BaseModel):
    """Configuration model for the project section of Unreal."""

    uproject_path: Path = Field(description="The path to the .uproject file of the Unreal project.")

    def get_uproject_folder_path(self) -> Path:
        """Get the absolute path to the uproject folder."""
        return self.uproject_path.parent.resolve()

    # Done like this to make it optional in the config file
    # but will try to be set to a relative path from the uproject_path

    @model_validator(mode="after")
    def validate_model(self, info: ValidationInfo) -> "UnrealProjectConfig":
        """Validation of the project config model
        and try to resolve paths to the uproject file."""
        if not info.context or not info.context.config_file_path:
            raise ValueError("A context with a config_file_path is required")

        if not self.uproject_path.is_absolute():
            # Resolve relative to config file directory
            config_dir = Path(info.context.config_file_path).parent
            self.uproject_path = (config_dir / self.uproject_path).resolve()
            logger.debug(
                "Resolved uproject_path relative to config file: %s",
                self.uproject_path,
            )

        if not self.uproject_path.is_file():
            raise ValueError("uproject_path does not point to a valid file")

        logger.info("Resolved uproject_path: %s", self.uproject_path)

        return self


class UnrealConfig(FeatureConfig):
    """Configuration model for the unreal feature."""

    project: UnrealProjectConfig = Field(description="The Unreal project configuration.")
    buildgraph: UnrealBuildGraphConfig = Field(description="The buildgraph configuration.")
    cleanup_after_build: Optional[UnrealCleanupConfig] = Field(default=None, description="Options to run post-buildgraph cleanup tasks.")


class UnrealFeature(BaseFeature):
    """Feature for using Unreal Engine."""

    feature_name = "unreal"

    def should_include(self, config: Dict[str, Any]) -> bool:
        return "unreal" in config

    def get_config_model(self) -> Type[FeatureConfig]:
        return UnrealConfig

    @property
    def dependencies(self) -> List[str]:
        return ["python", "utils"]

    def render_block(self, block_type: str, context: TemplateContext, template: Template) -> str:
        if block_type == "build_steps":
            jenkins_jobs = self.get_jenkins_jobs(context)
            context.feature_config._accumulator["jenkins_jobs_output"] = jenkins_jobs

            unreal_config: UnrealConfig = cast(UnrealConfig, context.feature_config)

            # list of all the properties to pass to buildgraph, one per line.
            # The character ` at the end of each line is important for the powerShell call
            buildgraph_properties: str = ""
            if unreal_config.buildgraph.properties is not None:
                lines = [f"-set:{key}={value}" for key, value in unreal_config.buildgraph.properties.items()]
                buildgraph_properties += " `\n".join(lines)

            context.feature_config._accumulator["buildgraph_properties"] = buildgraph_properties

        return super().render_block(block_type, context, template)

    def _generate_buildgraph_export_file(self, context: TemplateContext) -> Path:
        config: UnrealConfig = cast(UnrealConfig, context.feature_config)
        temp_dir: Path = Path(tempfile.gettempdir())
        export_path = temp_dir.joinpath("buildgraph.json")

        cwd = str(config.project.get_uproject_folder_path() / f"{context.full_config.features['python']['venv_folder']}/Scripts/")

        args: List[str] = [f"{cwd}/ue-run-buildgraph.exe", f"--target={config.buildgraph.target}", f"-Export={export_path}", "uebp_UATMutexNoWait=1"]

        if config.buildgraph.properties:
            args += [f'-set:{k}="{v}"' if " " in str(v) else f"-set:{k}={v}" for k, v in config.buildgraph.properties.items()]

        process = subprocess.Popen(args, stdout=subprocess.PIPE)

        result = process.wait()

        if result != 0:
            raise RuntimeError(f"Buildgraph export command failed with exit code {result}")

        return export_path

    def get_jenkins_jobs(self, context: TemplateContext) -> str:
        """Generate the Jenkins jobs for Unreal."""

        export_path = self._generate_buildgraph_export_file(context)

        class UnrealBuildgraphJsonOutput_Notify(BaseModel):
            """Notification configuration for a node."""

            default: str = Field(alias="Default")
            submitters: str = Field(alias="Submitters")
            warnings: bool = Field(alias="Warnings")

            class Config:
                populate_by_name = True

        class UnrealBuildgraphJsonOutput_Node(BaseModel):
            """Represents a build node within a group."""

            name: str = Field(alias="Name")
            depends_on: list[str] = Field(alias="DependsOn")
            run_early: bool = Field(alias="RunEarly")
            notify: UnrealBuildgraphJsonOutput_Notify = Field(alias="Notify")

            @field_validator("depends_on", mode="before")
            @classmethod
            def split_depends_on(cls, v: str) -> list[str]:
                """Convert semicolon-separated string to list."""
                if isinstance(v, str):
                    # Split by semicolon and filter out empty strings
                    return [dep.strip() for dep in v.split(";") if dep.strip()]
                return v

            class Config:
                populate_by_name = True

        class UnrealBuildgraphJsonOutput_Group(BaseModel):
            """Represents a build group containing nodes."""

            name: str = Field(alias="Name")
            agent_types: List[str] = Field(alias="Agent Types")
            nodes: List[UnrealBuildgraphJsonOutput_Node] = Field(alias="Nodes")

            class Config:
                populate_by_name = True

        class UnrealBuildgraphJsonOutput_BuildAgent(BaseModel):
            """Represents a build agent with its associated groups."""

            agent_type: str
            groups: Dict[str, UnrealBuildgraphJsonOutput_Group]
            parallel_groups: List[List[str]] = Field(default_factory=list, exclude=True)

            class Config:
                arbitrary_types_allowed = True

            @model_validator(mode="after")
            def create_parallel_groups(self) -> "UnrealBuildgraphJsonOutput_BuildAgent":
                job_to_group: dict[str, str] = {}

                for group in self.groups.values():
                    for node in group.nodes:
                        job_to_group.update({node.name: group.name})

                g = Graph()

                for group_name, group in self.groups.items():
                    for node in group.nodes:
                        for dependency in node.depends_on:
                            required_group_name = job_to_group[dependency]
                            if required_group_name != group_name:
                                g.add_edge(group_name, required_group_name)

                self.parallel_groups = g.topological_sort_with_hierarchy()

                return self

        class UnrealBuildgraphJsonOutput_BuildConfiguration(BaseModel):
            """Root configuration for the build system."""

            groups: List[UnrealBuildgraphJsonOutput_Group] = Field(alias="Groups")
            badges: List[str] = Field(alias="Badges")
            reports: List[str] = Field(alias="Reports")
            build_agents: Dict[str, UnrealBuildgraphJsonOutput_BuildAgent] = Field(default_factory=dict, exclude=True)

            class Config:
                populate_by_name = True

            @model_validator(mode="after")
            def create_build_agents(self) -> "UnrealBuildgraphJsonOutput_BuildConfiguration":
                """Create BuildAgent objects by grouping Groups by their agent types."""
                agent_map: Dict[str, Dict[str, UnrealBuildgraphJsonOutput_Group]] = {}

                for group in self.groups:
                    for agent_type in group.agent_types:
                        if agent_type not in agent_map:
                            agent_map[agent_type] = {}
                        agent_map[agent_type][group.name] = group

                self.build_agents = {
                    agent_type: UnrealBuildgraphJsonOutput_BuildAgent(agent_type=agent_type, groups=groups)
                    for agent_type, groups in agent_map.items()
                }

                return self

            @staticmethod
            def create_from_path(path: Path) -> "UnrealBuildgraphJsonOutput_BuildConfiguration":
                with open(path, encoding="utf-8") as f:
                    json_str = f.read()
                    return UnrealBuildgraphJsonOutput_BuildConfiguration.model_validate_json(json_str)

        build_configuration = UnrealBuildgraphJsonOutput_BuildConfiguration.create_from_path(export_path)

        TEMPLATE = """
    def buildgraph_job_groups = [
% for build_agent_platform,build_agent in ctx.build_agents.items():
    % for group in build_agent.parallel_groups:
        [
        % for group_name in group:
            [
                "${group_name}": [
                    tasks: [ ${", ".join(f'"{node.name}"' for node in build_agent.groups[group_name].nodes)} ],
                    platform: "${build_agent_platform}"
                ],
            ],
        % endfor
        ],
    % endfor
% endfor
    ]

    buildgraph_job_groups.each { group ->
        executeJobsInParallel(group)
    }
"""

        jobs_template = Template(TEMPLATE)
        return str(jobs_template.render(ctx=build_configuration))
