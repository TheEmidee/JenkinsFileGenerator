# GitHubConfig

```
Configuration for the GitHub feature.
```
  * **owner**: The GitHub owner of the repository. (  Type: `str` )

  * **repository**: The GitHub repository name. (  Type: `str` )

  * **credentials_id**: The jenkins credentials id that is associated with the GITHUB_TOKEN. (  Type: `str` )

  * **pull_requests**: Configuration for the pull requests (  Type: `Optional[features.github.GitHubPullRequestConfig]` Default: `None` )
    * **filter**: Filter configuration for pull requests, e.g., tokens to ignore. (  Type: `Optional[features.github.GitHubPullRequestFilterConfig]` Default: `None` )
      * **tokens**: List of tokens to ignore in pull requests, e.g., 'WIP', 'NO_CI'. (  Type: `Optional[List[str]]` Default: `None` )

      * **message**: Custom message to display when a pull request is ignored due to the filter. (  Type: `str` )


    * **update_description_from_pr_body**: If true, updates the current build description with the body of the pull request. (  Type: `Optional[bool]` Default: `None` )


[Back to main page](index.md)