# GitConfig

```
Configuration model for the git properties.
```
  * **use_simple_checkout**: Set to true to uses a simple `checkout scm`. Otherwise fine-tune the checkout with the other properties (  Type: `bool` Default: `True` )

  * **checkout**: The checkout configuration. If use_simple_checkout is true, this will be ignored. (  Type: `Optional[features.git.GitCheckoutConfig]` Default: `None` )
    * **branch_name**: The branch name to checkout (  Type: `str` )

    * **extensions**: The extensions to use for the checkout (  Type: `Dict[str, GitExtensionConfig]` Default: `{}` )


    * **user_remote_config**: The user remote configuration. (  Type: `UserRemoteConfig` )
      * **credentials_id**: The credentials ID and URL for the remote repository. (  Type: `CredentialsIdConfig` )
        * **id**: The jenkins credential id to use to connect to the url. (  Type: `str` )

        * **url**: The git url to use to checkout the repository. (  Type: `str` )




[Back to main page](index.md)