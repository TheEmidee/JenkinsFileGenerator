"""This feature works by using Buildgraph in an Unreal Engine project.
It requires that you use
* UEProjectBootStrap : https://github.com/TheEmidee/UEProjectBootstrap
* PyScripts https://github.com/TheEmidee/UEPyScripts

If you set the property `use_parallel_jobs` from `buildgraph` to false, then the output is simple:
It will execute `ue-ci-run-buildgraph` (from UEPyScripts) to run the target defined in the config, passing it the various arguments
and properties.

`ue-ci-run-buildgraph` internally calls `ue-run-buildgraph`, passing down a few extra arguments, such as `-Nop4` and `BuildMachine`.

If you choose to set `use_parallel_jobs` to true, then this package will execute a pre-pass to generate a list of tasks from the buildgraph file
that can be executed in parallel.

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

from pathlib import Path
from typing import Any, Dict, List, Optional, Type, cast

from pydantic import BaseModel, Field, ValidationInfo, model_validator

from generator import logger
from generator.core.base_feature import BaseFeature, FeatureConfig
from generator.core.template_context import TemplateContext
from generator.features.unreal_buildgraph import BuildGraphExporter, UEPyScriptsExporter, plan_buildgraph


class UnrealBuildGraphConfig(BaseModel):
    """Configuration for Unreal Build Graph tasks."""

    script: Optional[Path] = Field(
        default=None,
        description=(
            "Path to the XML file. If not set, will use the info from Config/PyScripts/config.ini of the game project."
            "This can be an absolute path, or relative to the yaml config file used to generate the jenkinsfile"
        ),
    )
    target: str = Field(description="The target to build with Build Graph.")
    use_parallel_jobs: bool = Field(
        default=True,
        description=(
            "If set to true, a pre-pass will execute buildgraph to output a json which will be analyzed to sort tasks by dependencies"
            "to execute them in parallel. (For ex compile all targets in parallel, then cook all targets in parallel, etc...)"
            "Set this property to false to disable this prepass and simply execute the target"
        ),
    )
    node_name_filters: Optional[Dict[str, str]] = Field(
        default=None,
        description=(
            "Filters to apply to the node names. Keys are the buildgraph task names and values are the jenkins node filter."
            "(Ex: `'MyGame Editor Win64 Test=BootTest': '!NoGPU'` will not select machine with no GPU to run the BootTest)"
        ),
    )
    arguments: Optional[List[str]] = Field(
        default=None,
        description="Arguments to pass to build graph. These are passed as is.",
    )
    properties: Optional[Dict[str, str]] = Field(
        default=None,
        description="Properties to pass to build graph. These are passed as -set:PropertyName=PropertyValue arguments.",
    )
    pre_tasks: Optional[List[str]] = Field(
        default=[],
        description="List of tasks to run before the buildgraph tasks.",
    )

    @model_validator(mode="after")
    def validate_model(self, info: ValidationInfo) -> "UnrealBuildGraphConfig":
        """Validation of the buildgraph config model
        and try to resolve paths to the script file if set."""
        if not info.context or not info.context.config_file_path:
            raise ValueError("A context with a config_file_path is required")

        if self.script:
            if not self.script.is_absolute():
                # Resolve relative to config file directory
                config_dir = Path(info.context.config_file_path).parent
                self.script = (config_dir / self.script).resolve()
                logger.debug(
                    "Resolved script relative to config file: %s",
                    self.script,
                )

            if not self.script.is_file():
                raise ValueError("script does not point to a valid file")

            logger.info("Resolved script: %s", self.script)

        return self


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

    uproject_path: Path = Field(
        description=(
            "The path to the .uproject file of the Unreal project."
            "This can be an absolute path to a uproject file, or relative to the yaml config file used to generate the jenkinsfile"
        )
    )

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


class UnrealAutomationConfigConfig(BaseModel):
    """Configuration for the automation scripts."""

    logs_folder: Optional[str] = Field(
        default="",
        description=(
            "Path to save the logs."
            "This is defined by setting the environment variable uebp_LogFolder before executing any automation script."
            "For ex: ${env.WORKSPACE}/Saved/Logs/"
        ),
    )


class UnrealConfig(FeatureConfig):
    """Configuration model for the unreal feature."""

    project: UnrealProjectConfig = Field(description="The Unreal project configuration.")
    buildgraph: UnrealBuildGraphConfig = Field(description="The buildgraph configuration.")
    cleanup_after_build: Optional[UnrealCleanupConfig] = Field(default=None, description="Options to run post-buildgraph cleanup tasks.")
    automation: Optional[UnrealAutomationConfigConfig] = Field(default=None, description="Options to configure the automation scripts.")


class UnrealFeature(BaseFeature):
    """Feature for using Unreal Engine."""

    feature_name = "unreal"

    def __init__(self, exporter: Optional[BuildGraphExporter] = None) -> None:
        self._exporter: BuildGraphExporter = exporter if exporter is not None else UEPyScriptsExporter()

    def should_include(self, config: Dict[str, Any]) -> bool:
        return "unreal" in config

    def get_config_model(self) -> Type[FeatureConfig]:
        return UnrealConfig

    @property
    def dependencies(self) -> List[str]:
        return ["python", "utils"]

    def get_template_values(self, context: TemplateContext) -> Dict[str, Any]:
        """Hand the BuildGraph plan to unreal.mako (None when parallel jobs are disabled)."""
        config = cast(UnrealConfig, context.feature_config)
        plan = plan_buildgraph(config.buildgraph, config.project.uproject_path, self._exporter) if config.buildgraph.use_parallel_jobs else None
        return {"buildgraph_plan": plan}
