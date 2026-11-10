"""Tests for the BuildGraph plan, through `plan_buildgraph`, its exporters, and the Unreal feature's rendering."""

import json
from pathlib import Path
from typing import Any, Dict, List, Sequence

import pytest
from conftest import WriteConfig
from mako.lookup import TemplateLookup  # type: ignore[import-untyped]

from generator.core import constants
from generator.core.pipeline_loading import load_pipeline
from generator.core.template_context import TemplateContext
from generator.core.validation_context import ConfigValidationContext
from generator.features import unreal_buildgraph
from generator.features.unreal import UnrealBuildGraphConfig, UnrealFeature
from generator.features.unreal_buildgraph import JobGroup, UEPyScriptsExporter, plan_buildgraph

FIXTURES = Path(__file__).parent / "fixtures"


class FixtureExporter:
    """Test adapter: records the arguments it was asked to export with and returns a fixed export."""

    def __init__(self, export_text: str) -> None:
        self.export_text = export_text
        self.requests: List[List[str]] = []

    def export(self, arguments: Sequence[str]) -> str:
        self.requests.append(list(arguments))
        return self.export_text


def fixture_exporter() -> FixtureExporter:
    return FixtureExporter((FIXTURES / "buildgraph_export.json").read_text(encoding="utf-8"))


def export_of(groups: List[Dict[str, Any]]) -> str:
    """A minimal BuildGraph export. Each group: {"name", "agents", "nodes": {node_name: "Dep A;Dep B"}}."""
    notify = {"Default": "", "Submitters": "", "Warnings": True}
    return json.dumps(
        {
            "Groups": [
                {
                    "Name": group["name"],
                    "Agent Types": group["agents"],
                    "Nodes": [{"Name": name, "DependsOn": deps, "RunEarly": False, "Notify": notify} for name, deps in group["nodes"].items()],
                }
                for group in groups
            ],
            "Badges": [],
            "Reports": [],
        }
    )


def buildgraph_config(tmp_path: Path, **values: Any) -> UnrealBuildGraphConfig:  # noqa: ANN401
    return UnrealBuildGraphConfig.model_validate({"target": "Nightly", **values}, context=ConfigValidationContext(tmp_path / "pipeline.yaml"))


def names(batches: Sequence[Sequence[JobGroup]]) -> List[List[str]]:
    return [[job_group.name for job_group in batch] for batch in batches]


def test_export_request_carries_project_script_target_and_quoted_properties(tmp_path: Path) -> None:
    script = tmp_path / "BuildGraph.xml"
    script.write_text("<BuildGraph/>", encoding="utf-8")
    exporter = fixture_exporter()
    config = buildgraph_config(tmp_path, script="BuildGraph.xml", properties={"Platform": "Win64", "Description": "Nightly build"})

    plan_buildgraph(config, Path("C:/Game/MyGame.uproject"), exporter)

    assert exporter.requests == [
        [
            f"--uproject={Path('C:/Game/MyGame.uproject')}",
            f"--script={script.resolve()}",
            "--target=Nightly",
            "uebp_UATMutexNoWait=1",
            "-set:Platform=Win64",
            '-set:Description="Nightly build"',
        ]
    ]


def test_export_request_without_script_or_properties(tmp_path: Path) -> None:
    exporter = fixture_exporter()

    plan_buildgraph(buildgraph_config(tmp_path), Path("Game.uproject"), exporter)

    assert exporter.requests == [["--uproject=Game.uproject", "--script=", "--target=Nightly", "uebp_UATMutexNoWait=1"]]


def test_groups_are_ordered_into_batches_per_agent_type(tmp_path: Path) -> None:
    plan = plan_buildgraph(buildgraph_config(tmp_path), Path("Game.uproject"), fixture_exporter())

    assert names(plan.batches) == [
        ["Editor Win64", "Game Win64"],
        ["Cook Win64"],
        ["Tests Win64"],
        ["Game Linux"],
    ]
    assert plan.batches[1] == (JobGroup("Cook Win64", ("Cook Game Win64", "Stage Win64"), "Win64"),)
    assert plan.batches[3] == (JobGroup("Game Linux", ("Compile Game Linux",), "Linux"),)


def test_dependencies_inside_a_group_do_not_split_it(tmp_path: Path) -> None:
    exporter = FixtureExporter(export_of([{"name": "Build", "agents": ["Win64"], "nodes": {"Compile": "", "Cook": "Compile", "Stage": "Cook"}}]))

    plan = plan_buildgraph(buildgraph_config(tmp_path), Path("Game.uproject"), exporter)

    assert plan.batches == ((JobGroup("Build", ("Compile", "Cook", "Stage"), "Win64"),),)


def test_known_limitation_cross_agent_type_dependency_is_rejected(tmp_path: Path) -> None:
    exporter = FixtureExporter(
        export_of(
            [
                {"name": "Editor Win64", "agents": ["Win64"], "nodes": {"Compile Editor": ""}},
                {"name": "Cook Linux", "agents": ["Linux"], "nodes": {"Cook Linux": "Compile Editor"}},
            ]
        )
    )

    with pytest.raises(ValueError, match="Compile Editor"):
        plan_buildgraph(buildgraph_config(tmp_path), Path("Game.uproject"), exporter)


def test_uepyscripts_exporter_exports_into_its_own_temporary_folder(monkeypatch: pytest.MonkeyPatch) -> None:
    export_paths: List[Path] = []

    def fake_main(argv: Sequence[str]) -> int:
        export_path = Path(next(arg for arg in argv if arg.startswith("-Export=")).split("=", 1)[1])
        export_paths.append(export_path)
        export_path.write_text('{"Groups": []}', encoding="utf-8")
        return 0

    monkeypatch.setattr(unreal_buildgraph.buildgraph, "main", fake_main)

    assert UEPyScriptsExporter().export(["--target=Nightly"]) == '{"Groups": []}'
    assert UEPyScriptsExporter().export(["--target=Nightly"]) == '{"Groups": []}'
    assert export_paths[0].parent != export_paths[1].parent
    assert not export_paths[0].parent.exists()


def test_uepyscripts_exporter_raises_when_the_export_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(unreal_buildgraph.buildgraph, "main", lambda argv: 3)

    with pytest.raises(RuntimeError, match="exit code 3"):
        UEPyScriptsExporter().export(["--target=Nightly"])


UNREAL_CONFIG = """\
pipeline_name: "UE"
project:
  name: "MyGame"
jenkins:
  default_node_names: "UE5"
features:
  unreal:
    project:
      uproject_path: "Game/MyGame.uproject"
    buildgraph:
      target: "Nightly"
      arguments: ["-Clean"]
      properties:
        Description: "Nightly build"
"""


def render_unreal(write_config: WriteConfig, tmp_path: Path, exporter: FixtureExporter, extra: str = "") -> Dict[str, List[str]]:
    (tmp_path / "Game").mkdir()
    (tmp_path / "Game" / "MyGame.uproject").write_text("{}", encoding="utf-8")
    result = load_pipeline(write_config(UNREAL_CONFIG + extra))
    assert result.pipeline is not None, result.messages

    context = TemplateContext(
        full_config=result.pipeline.config,
        feature_config=result.pipeline.feature_configs["unreal"],
        global_values={"output_feature_sections": False, "customization": {}},
    )
    lookup = TemplateLookup(directories=[str(constants.TEMPLATES_FOLDER)])
    return UnrealFeature(exporter=exporter).render_blocks(context, lookup).blocks


def test_unreal_feature_renders_the_plan_and_buildgraph_properties(write_config: WriteConfig, tmp_path: Path) -> None:
    exporter = fixture_exporter()

    blocks = render_unreal(write_config, tmp_path, exporter)

    assert len(exporter.requests) == 1
    [build_steps] = blocks["build_steps"]
    assert build_steps.startswith("def buildgraph_job_groups = [")
    assert '"Cook Win64": [\n                    tasks: [ "Cook Game Win64", "Stage Win64" ],\n                    platform: "Win64"' in build_steps
    assert build_steps.index('"Tests Win64"') < build_steps.index('"Game Linux"')
    [additional_functions] = blocks["additional_functions"]
    assert "-Clean `\n-set:Description=Nightly build `\n" in additional_functions
    assert "--no-single-node" not in additional_functions


def test_unreal_feature_without_parallel_jobs_does_not_export(write_config: WriteConfig, tmp_path: Path) -> None:
    exporter = fixture_exporter()

    blocks = render_unreal(write_config, tmp_path, exporter, extra="      use_parallel_jobs: false\n")

    assert exporter.requests == []
    assert blocks["build_steps"] == ['runBuildGraph("Nightly")']
    [additional_functions] = blocks["additional_functions"]
    assert "-Clean `\n--no-single-node `\n-set:Description=Nightly build `\n" in additional_functions
