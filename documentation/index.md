# PipelineConfig

```
Configuration for the Jenkins pipeline generator.
```
  * **pipeline_name**: Pipeline name. Used as an identifier at the top of the jenkinsfile (  Type: `str` )

  * **project**: Project Configuration (  Type: `ProjectConfig` )
    * **name**: The project name. Used in various places in the Jenkinsfile. (  Type: `str` )


  * **jenkins**: Jenkins Configuration (  Type: `JenkinsConfig` )
    * **workspace_suffix**: Suffix to append to the Jenkins workspace path (  Type: `Optional[str]` Default: `None` )

    * **default_node_names**: The names of the nodes to use by default by Jenkins for each stage (  Type: `str` )


  * **features**: All the features that you want to use in your jenkins file (  Type: `Dict[str, Any]` Default: `{}` )
# Features
- [GitConfig](gitconfig.md)
- [GitHubConfig](githubconfig.md)
- [PropertiesConfig](propertiesconfig.md)
- [SlackNotificationsConfig](slacknotificationsconfig.md)
- [UnrealConfig](unrealconfig.md)
- [UtilsConfig](utilsconfig.md)
