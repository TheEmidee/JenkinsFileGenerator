# GitConfig

```
This module defines the Git-related features and configurations for Jenkins pipelines.
```
  * **use_simple_checkout**: Set to true to uses a simple `checkout scm`. Otherwise fine-tune the checkout with the other properties (  Type: `bool` Default: `True` )

  * **checkout**: The checkout configuration. If use_simple_checkout is true, this will be ignored. (  Type: `Optional[features.git.GitCheckoutConfig]` Default: `None` )
    * **branch_name**: The branch name to checkout (  (Required) Type: `str` )

    * **extensions**: The extensions to use for the checkout (  Type: `Dict[str, GitExtensionConfig]` Default: `{}` )


    * **user_remote_config**: The user remote configuration. (  (Required) Type: `UserRemoteConfig` )
      * **credentials_id**: The credentials ID and URL for the remote repository. (  (Required) Type: `CredentialsIdConfig` )
        * **id**: The jenkins credential id to use to connect to the url. (  (Required) Type: `str` )

        * **url**: The git url to use to checkout the repository. (  (Required) Type: `str` )




  * **retry_count**: Set to a value greater than 1 to try to checkout multiple times. This can help avoid the job to fail in some circumstances (for example with a github app) (  Type: `Optional[int]` Default: `1` )

[Back to main page](index.md)