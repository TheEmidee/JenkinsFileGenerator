# JenkinsFileGenerator

A Python module that generates Jenkins pipeline files from YAML configuration files using a modular feature-based approach. This tool allows you to define complex Jenkins pipelines through declarative configuration while maintaining flexibility and reusability.

## Overview

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
pip install -r requirements.txt
```

## Usage

### Basic Command Line Usage

```bash
python -m generator <config_file> [options]
```

### Arguments

| Argument                   | Type | Required | Description                               |
| -------------------------- | ---- | -------- | ----------------------------------------- |
| `config`                   | Path | Yes      | Path to the YAML configuration file       |
| `-o, --output`             | Path | No       | Output path for the generated Jenkinsfile |
| `--lint`                   | Flag | No       | Run npm-groovy-lint on the generated file |
| `--generate_documentation` | Flag | No       | Generate configuration documentation      |

### Examples

```bash
# Basic generation
python -m generator config.yaml -o Jenkinsfile

# With linting
python -m generator config.yaml -o Jenkinsfile --lint

# Generate documentation
python -m generator config.yaml --generate_documentation
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

### Available Features

- **`utils`**: Basic utilities (abort running builds, etc.)
- **`properties`**: Jenkins pipeline properties
- **`git`**: Git checkout configuration
- **`github`**: GitHub integration (PR handling, status updates)
- **`slack_notifications`**: Slack messaging for build events
- **`unreal`**: Unreal Engine BuildGraph integration

See the `Samples/` directory for complete configuration examples.

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
def gitCheckout() {
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

    def get_config_model(self) -> BaseModel:
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

## License

MIT License - see LICENSE file for details.

## Contributing

1. Follow the existing feature pattern
2. Add appropriate validation and documentation
3. Include template tests
4. Update documentation

For detailed configuration options, see the generated documentation in the `documentation/` directory.
