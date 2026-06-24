# PipelineConfig

```
Configuration for the Jenkins pipeline generator.
This is what should be at the top of the config file.
It defines all the general settings, such as the project configuration,
the global jenkins configuration, and the features to be used in the pipeline.
```
  * **pipeline_name**: Pipeline name. Used as an identifier at the top of the jenkinsfile (  (Required) Type: `str` )

  * **customization_folder**: Path to a folder containing templates to use to override specific parts of some features.The path can be absolute, or relative to the config file (  Type: `Optional[pathlib.Path]` Default: `None` )

  * **project**: Project Configuration (  (Required) Type: `ProjectConfig` )
    * **name**: The project name. Used in various places in the Jenkinsfile. (  (Required) Type: `str` )


  * **jenkins**: Jenkins Configuration (  (Required) Type: `JenkinsConfig` )
    * **workspace_suffix**: Suffix to append to the Jenkins workspace path (  Type: `Optional[str]` Default: `None` )

    * **default_node_names**: The names of the nodes to use by default by Jenkins for each stage (  (Required) Type: `str` )


  * **features**: All the features that you want to use in your jenkins file (  Type: `Dict[str, Any]` Default: `{}` )
# Features
- [ArchiveConfig](archiveconfig.md)
- [GitConfig](gitconfig.md)
- [GitHubConfig](githubconfig.md)
- [PlasticSCMConfig](plasticscmconfig.md)
- [PropertiesConfig](propertiesconfig.md)
- [PythonConfig](pythonconfig.md)
- [SlackNotificationsConfig](slacknotificationsconfig.md)
- [UnrealConfig](unrealconfig.md)
- [UtilsConfig](utilsconfig.md)
