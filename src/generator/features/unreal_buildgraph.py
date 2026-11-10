"""BuildGraph plan for the Unreal feature.

Runs a BuildGraph export for the configured target (through an exporter), reads the export, and orders its
groups into Batches of Job groups that Jenkins can run in parallel.

Planning is done per agent type: each agent type's groups are ordered on their own, and the agent types follow
each other. A node depending on a node of another agent type is therefore rejected.
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Protocol, Sequence, Tuple

from pydantic import BaseModel, ConfigDict, Field, field_validator
from uepyscripts.run import buildgraph

from generator.utils.graph import build_dependency_graph

if TYPE_CHECKING:
    from generator.features.unreal import UnrealBuildGraphConfig


@dataclass(frozen=True)
class JobGroup:
    """One BuildGraph group as Jenkins runs it: its nodes run in order on one agent of `agent_type`."""

    name: str
    node_names: Tuple[str, ...]
    agent_type: str


@dataclass(frozen=True)
class BuildGraphPlan:
    """Ordered Batches of Job groups. Job groups in a Batch run in parallel; a Batch starts when the previous one is done."""

    batches: Tuple[Tuple[JobGroup, ...], ...]


class BuildGraphExporter(Protocol):
    """Produces a BuildGraph export (JSON text) for the given uepyscripts BuildGraph arguments."""

    def export(self, arguments: Sequence[str]) -> str:
        """Run the export and return its JSON text."""
        ...


class UEPyScriptsExporter:
    """Runs the export with uepyscripts (and therefore UAT), in a temporary folder of its own."""

    def export(self, arguments: Sequence[str]) -> str:
        with tempfile.TemporaryDirectory(prefix="buildgraph-export-") as temp_dir:
            export_path = Path(temp_dir) / "buildgraph.json"
            if (result := buildgraph.main([*arguments, f"-Export={export_path}"])) != 0:
                raise RuntimeError(f"Buildgraph export command failed with exit code {result}")
            return export_path.read_text(encoding="utf-8")


def plan_buildgraph(config: UnrealBuildGraphConfig, uproject_path: Path, exporter: BuildGraphExporter) -> BuildGraphPlan:
    """Export the BuildGraph target described by `config` and order its groups into a BuildGraph plan.

    Raises:
        RuntimeError: the export failed.
        pydantic.ValidationError: the export is not a valid BuildGraph export.
        ValueError: a node depends on a node that is not in its agent type's groups, or the dependencies form a cycle.
    """
    export = _BuildGraphExport.model_validate_json(exporter.export(_export_arguments(config, uproject_path)))

    groups_by_agent_type: Dict[str, Dict[str, _Group]] = {}
    for group in export.groups:
        for agent_type in group.agent_types:
            groups_by_agent_type.setdefault(agent_type, {})[group.name] = group

    batches: List[Tuple[JobGroup, ...]] = []
    for agent_type, groups in groups_by_agent_type.items():
        node_names = {name: [node.name for node in group.nodes] for name, group in groups.items()}
        dependencies: Dict[str, List[str]] = {}
        for group in groups.values():
            for node in group.nodes:
                for dependency in node.depends_on:
                    dependencies.setdefault(node.name, []).append(dependency)

        for batch in build_dependency_graph(node_names, dependencies):
            batches.append(tuple(JobGroup(name, tuple(node_names[name]), agent_type) for name in batch))

    return BuildGraphPlan(batches=tuple(batches))


def _export_arguments(config: UnrealBuildGraphConfig, uproject_path: Path) -> List[str]:
    arguments = [
        f"--uproject={uproject_path}",
        f"--script={config.script if config.script else ''}",
        f"--target={config.target}",
        "uebp_UATMutexNoWait=1",
    ]
    if config.properties:
        arguments += [f'-set:{key}="{value}"' if " " in str(value) else f"-set:{key}={value}" for key, value in config.properties.items()]
    return arguments


# --- BuildGraph export schema (as written by BuildGraph's -Export) -------------------------------


class _Notify(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    default: str = Field(alias="Default")
    submitters: str = Field(alias="Submitters")
    warnings: bool = Field(alias="Warnings")


class _Node(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(alias="Name")
    depends_on: List[str] = Field(alias="DependsOn")
    run_early: bool = Field(alias="RunEarly")
    notify: _Notify = Field(alias="Notify")

    @field_validator("depends_on", mode="before")
    @classmethod
    def split_depends_on(cls, value: object) -> object:
        """BuildGraph writes dependencies as one semicolon-separated string."""
        if isinstance(value, str):
            return [dependency.strip() for dependency in value.split(";") if dependency.strip()]
        return value


class _Group(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(alias="Name")
    agent_types: List[str] = Field(alias="Agent Types")
    nodes: List[_Node] = Field(alias="Nodes")


class _BuildGraphExport(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    groups: List[_Group] = Field(alias="Groups")
    badges: List[str] = Field(alias="Badges")
    reports: List[str] = Field(alias="Reports")
