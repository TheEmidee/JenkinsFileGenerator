# PlasticSCMConfig

```
This module defines the PlasticSCM-related features and configurations for Jenkins pipelines.
```
  * **checkout**: The checkout configuration. If use_simple_checkout is true, this will be ignored. (  (Required) Type: `PlasticSCMCheckoutConfig` )
    * **branch**: The branch name to checkout, overriden by shelveset and label. (  (Required) Type: `str` )

    * **changeset**: The changeset to checkout, overriden by shelveset and label. (  Type: `Optional[str]` Default: `None` )

    * **shelveset**: The shelveset to checkout, overrides branch and changeset, overriden by label. (  Type: `Optional[str]` Default: `None` )

    * **label**: The label to checkout, overrides branch, changeset and shelveset. (  Type: `Optional[str]` Default: `None` )

    * **changelog**: Enable or Disable 'Include in changelog'. (  Type: `Optional[bool]` Default: `True` )

    * **poll**: Enable or Disable 'Include in polling'. (  Type: `Optional[bool]` Default: `False` )

    * **remote_config**: The remote configuration. (  (Required) Type: `RemoteConfig` )
      * **repository**: The PlasticSCM repository name. (  (Required) Type: `str` )

      * **server**: The PlasticSCM server port. (  (Required) Type: `str` )


    * **cleanup**: Cleanup settings of the repository. (MINIMAL,STANDARD,FULL,DELETE) (  Type: `Optional[str]` Default: `STANDARD` )

    * **directory**: The workspace subdirectory to clone the repo, required if you use multiple workspaces. (  Type: `Optional[str]` Default: `None` )

    * **credentials_config**: The crendentials configuration. (  Type: `Optional[features.plasticscm.CredentialsConfig]` Default: `None` )
      * **working_mode**: The jenkins credential id working mode. (NONE,UP,LDAP) (  (Required) Type: `str` )

      * **credentials_id**: The jenkins credentials id to use to connect to the remote. (  (Required) Type: `str` )



[Back to main page](index.md)