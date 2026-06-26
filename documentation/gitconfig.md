# GitConfig

```
This module defines the Git-related features and configurations for Jenkins pipelines.
```
  * **checkout_code**: This property will be output in the jenkinsfile as is. You can generate a valid code by using the pipeline syntax page of Jenkins. (  Type: `str` Default: `checkout scm` )

  * **pre_checkout_tasks**: List of tasks to run before running the checkout. (  Type: `Optional[List[str]]` Default: `[]` )

  * **retry_count**: Set to a value greater than 1 to try to checkout multiple times. This can help avoid the job to fail in some circumstances (for example with a github app) (  Type: `Optional[int]` Default: `1` )

[Back to main page](index.md)