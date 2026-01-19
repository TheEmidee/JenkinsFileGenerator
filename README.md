# JenkinsFileGenerator

[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE) 
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/) 

---

## Overview ✅

JenkinsFileGenerator transforms YAML configuration files into complete Jenkins pipeline scripts (Jenkinsfiles) by combining multiple features such as Git checkout, GitHub integration, Slack notifications, Unreal Engine builds, and more. Each feature is implemented as a separate module with its own configuration schema and template, making the system highly extensible and maintainable.

## Features

- **Modular Feature System**: Each pipeline capability (Git, GitHub, Slack, etc.) is implemented as a separate feature
- **Dependency Resolution**: Automatic handling of feature dependencies using topological sorting
- **Template-based Generation**: Uses Mako templates for flexible code generation
- **Configuration Validation**: Pydantic-based validation for all configuration options
- **Documentation Generation**: Automatic generation of configuration documentation
- **Groovy Linting**: Optional integration with npm-groovy-lint for code quality

## Installation

1. Clone the repository
2. Set up the Python environment:

```powershell
# Windows PowerShell
.\setup-env.ps1

# Or manually:
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .[dev]
```

## Usage

### Basic Command Line Usage

Activating the virtual environment will create a script named jenkinsfilegenerator that you can use:

```bash
jenkinsfilegenerator <config_file> [options]
```

### Arguments

| Argument                   | Type | Required | Description                                        |
| -------------------------- | ---- | -------- | ---------------------------------------------------|
| `config`                   | Path | Yes      | Path to the YAML configuration file                |
| `-o, --output`             | Path | Yes      | Output path for the generated Jenkinsfile          |
| `--batch`                  | Path | No       | Path to a YAML batch file                          |
| `-bbd, --blackboarddata`   | Str  | No       | A comma separated list of key=value pairs          |
| `--lint`                   | Flag | No       | Run npm-groovy-lint on the generated file          |
| `--generate-documentation` | Flag | No       | Generates the configuration documentation          |
| `--validate`               | Flag | No       | Validates the config file and the mako templates   |
| `--list_features`          | Flag | No       | Output the registered features in the console      |
| `--no-validation`          | Flag | No       | Skip configuration validation (not recommended)    |
| `--verbose`                | Flag | No       | Show detailed messages                             |
| `--quiet`                  | Flag | No       | Suppress non-error output                          |

### Examples

```bash
# Basic generation
jenkinsfilegenerator config.yaml -o Jenkinsfile

# With linting
jenkinsfilegenerator config.yaml -o Jenkinsfile --lint

# With the blackboard data
jenkinsfilegenerator config.yaml -o Jenkinsfile --blackboarddata "build_type=Development,platform=Windows" --lint

# Use a batch file with linting
jenkinsfilegenerator --batch batch.yaml --lint

# Generate documentation
jenkinsfilegenerator config.yaml --generate_documentation
```

## Blackboard data

If you need to use the same token multiple times in a YAML config file, it is possible to specify that token in the blackboard data, with the `--blackboarddata` argument, which accepts a comma separated list of key=value pairs.

For example `build_type=Development,platform=Windows`.

In your config file, you can use the syntax `^BLACKBOARD_DATA.key^`.

So for example if in your config file you have the following text:

```
pipeline_name: "MyGame_^BLACKBOARD_DATA.build_type^"
project:
  name: "MyGame"
jenkins:
  default_node_names: "UE_5.2"
features:
  git:
    use_simple_checkout: false
    checkout:
      branch_name: "refs/heads/^BLACKBOARD_DATA.branch_name^"
```

You can pass the string `build_type=Development,branch_name=develop`, which will update the config file to 

```
pipeline_name: "MyGame_Development"
project:
  name: "MyGame"
jenkins:
  default_node_names: "UE_5.2"
features:
  git:
    use_simple_checkout: false
    checkout:
      branch_name: "refs/heads/develop"
```

before using this updated version of the config file to generate the final jenkinsfile.

## Batch generation

Instead of using the `config` and `--output` arguments to generate a single jenkinsfile, it's possible to use the `--batch` argument to specify the path to a YAML file which contains a list of items which will each generate a different jenkinsfile.

The structure of the YAML file should start with an `items` property, which is an array of `input_config_file`, `output_jenkinsfile` and `blackboard_data`. The `input_config_file` and `output_jenkinsfile` properties are both relative path to the batch config file.

```
items:
- input_config_file: "jenkinsfile_release_template.yaml"
  output_jenkinsfile: "../Jenkinsfile_Release_Development"
  blackboard_data: "build_type=Development,branch_name=develop"
- input_config_file: "jenkinsfile_release_template.yaml"
  output_jenkinsfile: "../Jenkinsfile_Release_Staging"
  blackboard_data: "build_type=Staging,branch_name=staging"
- input_config_file: "jenkinsfile_release_template.yaml"
  output_jenkinsfile: "../Jenkinsfile_Release_Production"
  blackboard_data: "build_type=Production,branch_name=release"
```

This is a great way to generate, from the same template file, multiple outputs with different values, in one command, without having to maintain multiple config files.

## Customizing the output

Some features have entry points in the output they generate, to allow you to define custom code for your project.

You can find those entry points by looking for code like this in the mako files of this repository:

```
% if global_values['customization'].get('XXX'):
<%include file="${global_values['customization']['XXX']}"/>
% endif
```

To output your own code, you need to follow these simple steps:

1. Create a folder next to your config file that will contain your customization code (Ex: `Customization`)
2. Set the property `customization_folder` of your pipeline config to the name of your folder (If you place that folder in another location, you can use a relative path here. You can also use an absolute path if you want)
3. In that folder, create a file for each customization you want. For example, the unreal feature supports `unreal_postBuildGraphTasks`. So you would create a file named `unreal_postBuildGraphTasks.mako` in that folder. Note that you can use the context data that the mako template engine uses, so you have the exact same data that is used when the feature is processed.

That's it !

You can check [ue_full_example.yaml](examples/ue_full_example.yaml) for a working configuration.

## How to debug?

### VS Code

In the `launch.json` file of the `.vscode` folder, add the following lines:

```
{
  "configurations": [
    {
      "name": "Python Debugger: Module",
      "type": "debugpy",
      "request": "launch",
      "module": "generator",
      "console": "integratedTerminal",
      "args": [
        "E:/Dev/Projects/YourGame/Scripts/Build/Jenkins/Config/jenkinsfile_pull_request.yaml",
        "--output",
        "E:/Dev/Projects/YourGame/Scripts/Build/Jenkins/Jenkinsfile",
        "--lint"
      ]
    }
  ]
}
```

## Configuration File Structure

The configuration file is a YAML file with the following top-level structure:

```yaml
pipeline_name: "MyPipeline"
project:
  name: "MyProject"
jenkins:
  default_node_names: "linux"
  workspace_suffix: "optional_suffix"
features:
  # Feature configurations go here
```

See the [examples](examples) directory for configuration examples.

### Available Features

- **`utils`**: Basic utilities (abort running builds, etc.)
- **`properties`**: Jenkins pipeline properties
- **`git`**: Git checkout configuration
- **`github`**: GitHub integration (PR handling, status updates)
- **`plasticscm`**: PlasticSCM checkout configuration
- **`slack_notifications`**: Slack messaging for build events
- **`unreal`**: Unreal Engine BuildGraph integration

You can also look at the [documentation](documentation/index.md) for the features.

## How the Feature System Works

### 1. Configuration to Feature Selection

When you provide a YAML configuration file, the generator:

1. **Parses the YAML** into a `PipelineConfig` object
2. **Discovers available features** by scanning the `generator/features/` directory
3. **Selects active features** based on what's present in the `features` section of your config
4. **Validates configuration** for each selected feature using Pydantic models

```python
# Example: If your config has this...
features:
  git:
    use_simple_checkout: true
  slack_notifications:
    channel: "#ci-builds"
    message_template: "Build completed"

# The generator will:
# 1. Instantiate GitFeature and SlackNotificationsFeature
# 2. Validate their configurations against GitConfig and SlackNotificationsConfig
# 3. Add any missing dependencies (utils is added automatically)
```

### 2. Dependency Resolution

Features can declare dependencies on other features:

```python
class GitHubFeature(BaseFeature):
    feature_name = "github"

    @property
    def dependencies(self) -> List[str]:
        return ["utils"]  # GitHub feature requires utils feature
```

The system uses topological sorting to ensure features are processed in the correct order, automatically adding missing dependencies with default configurations.

### 3. Template-based Code Generation

Each feature has an associated Mako template in `generator/templates/` that defines code blocks:

```mako
<!-- git.mako -->
<%def name="additional_functions()">
def checkout() {
    % if feature_config.use_simple_checkout:
        checkout scm
    % else:
        // Complex checkout logic here
    % endif
}
</%def>
```

### 4. Block Assembly

Each feature can contribute to these predefined blocks in the final Jenkinsfile:

- **`libraries`**: @Library imports
- **`imports`**: Import statements
- **`properties`**: Pipeline properties
- **`pre_pipeline_steps`**: Code before main pipeline
- **`build_steps`**: Main build logic
- **`on_build_unstable`**: Unstable build handling
- **`on_build_failure`**: Failure handling
- **`on_build_success`**: Success handling
- **`post_build_steps`**: Post-build cleanup
- **`on_exception_thrown`**: Exception handling
- **`on_finally`**: Finally block
- **`additional_functions`**: Helper functions

### 5. Final Assembly

The base template (`base_jenkinsfile.mako`) combines all feature blocks into the final Jenkinsfile:

```groovy
// Generated structure
@Library('feature-libs')
import feature.imports

properties([...])

try {
    // pre_pipeline_steps from all features

    // build_steps from all features

    if (currentBuild.result == 'UNSTABLE') {
        // on_build_unstable from all features
    } else if (currentBuild.result == 'FAILURE') {
        // on_build_failure from all features
    } else {
        // on_build_success from all features
    }

} catch (Exception e) {
    // on_exception_thrown from all features
    throw e
} finally {
    // on_finally from all features
}

// additional_functions from all features
```

### 6. Feature Implementation Pattern

To create a new feature:

1. **Create the configuration model**:

```python
class MyFeatureConfig(FeatureConfig):
    setting1: str = Field(description="Description here")
    setting2: Optional[bool] = Field(default=False)
```

2. **Implement the feature class**:

```python
class MyFeature(BaseFeature):
    feature_name = "my_feature"

    def should_include(self, config: Dict[str, Any]) -> bool:
        return "my_feature" in config

    def get_config_model(self) -> Type[FeatureConfig]::
        return MyFeatureConfig

    @property
    def dependencies(self) -> List[str]:
        return ["utils"]  # Optional dependencies
```

3. **Create the template** (`templates/my_feature.mako`):

```mako
<%def name="build_steps()">
    // Your Jenkins pipeline code here
    echo "Running my feature with setting: ${feature_config.setting1}"
</%def>
```

The feature will be automatically discovered and available for use in configuration files.

## Development

### Project Structure

```
generator/
├── core/                    # Core engine components
│   ├── jenkins_file_generator.py  # Main orchestrator
│   ├── base_feature.py      # Feature base class
│   ├── dependency_resolver.py     # Dependency management
│   └── ...
├── features/                # Feature implementations
│   ├── git.py
│   ├── github.py
│   ├── slack_notifications.py
│   └── ...
├── templates/               # Mako templates
│   ├── base_jenkinsfile.mako
│   ├── git.mako
│   └── ...
└── utils/                   # Utility modules
```

### Adding New Features

1. Create your feature class in `generator/features/`
2. Create your template in `generator/templates/`
3. The feature will be automatically discovered and registered
4. Run `--generate_documentation` to update docs

### Code validation

You can use `ruff` with `ruff check .` and `mypy` with `mypy .` to validate that the code is correct before submitting.

### Code Formatting

You can use `ruff format .` to automatically reformat the code.

## License

MIT License - see LICENSE file for details.

## Contributing

1. Follow the existing feature pattern
2. Add appropriate validation and documentation
3. Include template tests
4. Update documentation

For detailed configuration options, see the generated documentation in the `documentation/` directory.
