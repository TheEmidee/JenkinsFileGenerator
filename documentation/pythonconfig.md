# PythonConfig

```
This module defines the python feature for Jenkins pipelines.

This feature will create 2 additional functions:
* activatePythonEnvironment which will call the script defined in the config with the venv_activation_script_path
* executePythonScript which will execute an executable in the virtual environment's Scripts folder
```
  * **venv_activation_script_path**: The path to the virtual environment activation script.This must point to a script that can be sourced to activate the virtual environment. (  Type: `Optional[str]` Default: `None` )

  * **venv_folder**: The path to the virtual environment folder after it has been created by executing venv_activation_script_path. (  (Required) Type: `str` )

[Back to main page](index.md)