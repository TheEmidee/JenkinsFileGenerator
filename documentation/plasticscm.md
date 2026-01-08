# PlasticSCMConfig

```
This module defines the PlasticSCM-related features and configurations for Jenkins pipelines with [PlasticSCM Plugin](https://plugins.jenkins.io/plasticscm-plugin/).
```
  * **checkout**: The checkout configuration. (  (Required) Type: `PlasticSCMCheckoutConfig` Default: `None` )
    * **branch**: The branch to checkout. (  (Required) Type: `str` )

    * **changeset**: The changeset to checkout, overriden by shelveset and label. (  (Optionnal) Type: `str` Default: `None` )

    * **shelveset**: The shelveset to checkout, overrides branch and changeset, overriden by label. (  (Optionnal) Type: `str` Default: `None` )

    * **label**: The label to checkout, overrides branch, changeset and shelveset. (  (Optionnal) Type: `str` Default: `None` )

    * **changelog**: Enable or Disable 'Include in changelog' (  (Optional) Type: `bool` Default: `True` )

    * **poll**: Enable or Disable 'Include in polling' (  (Optional) Type: `bool` Default: `False` )

    * **remote_config**: The remote configuration. (  (Required) Type: `RemoteConfig` )
      * **repository**: The PlasticSCM repository name. (  (Required) Type: `str` )

      * **server**: The PlasticSCM server port. (  (Required) Type: `str` )


    * **cleanup**: Cleanup settings of the repository. (MINIMAL,STANDARD,FULL,DELETE) (  (Optional) Type: `str` Default: `STANDARD` )

    * **directory**: The workspace subdirectory to clone the repo, required if you use multiple workspaces. (  (Optional) Type: `str` Default: `None` )

    * **credentials_config**: The crendentials configuration. (  (Optional) Type: `CredentialsConfig` )
      * **working_mode**: The jenkins credential id working mode. (NONE,UP,LDAP) (  (Required) Type: `str` )

      * **credentials_id**: The jenkins credentials id to use to connect to the remote. (  (Required) Type: `str` )


[Back to main page](index.md)