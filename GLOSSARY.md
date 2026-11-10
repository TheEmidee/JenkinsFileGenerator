# Glossary

Domain language for JenkinsFileGenerator. Use these terms in code, issues, and reviews.

**Pipeline config**: the YAML file a user writes to describe one Jenkinsfile, and its validated model (`PipelineConfig`): pipeline name, project, jenkins settings, optional Customization folder, and the `features` section.
_Avoid_: input file, settings file.

**Feature**: a self-contained unit of Jenkinsfile behaviour (git, github, unreal, slack_notifications, ...). Declared by a key under `features:` in the Pipeline config, implemented by a `BaseFeature` subclass and a Mako template of the same name.
_Avoid_: plugin, module (reserved for code design).

**Feature config**: the validated settings of one Feature, taken from its key under `features:` (a `FeatureConfig` subclass).

**Blackboard data**: `key=value` pairs supplied on the command line or per Generation item, substituted into the Pipeline config text wherever `^BLACKBOARD_DATA.key^` appears, before the YAML is parsed.

**Customization folder**: an optional folder of user `.mako` files, resolved relative to the Pipeline config, used to override or extend parts of Feature templates.

**Generation item**: one (Pipeline config, output Jenkinsfile, Blackboard data) triple. A batch file lists several.

**Pipeline loading**: turning a Pipeline config file plus Blackboard data into a Loaded pipeline or a list of Validation messages. The only place a Pipeline config is parsed (see ADR-0001).

**Loaded pipeline**: the result of successful Pipeline loading: the validated Pipeline config, the Feature config of every declared Feature, and where it came from (source file, Blackboard data).

**Validation message**: one located finding (error, warning, or info) about a Pipeline config or a template: message, file, line, the config key path it concerns, and an optional suggestion.
