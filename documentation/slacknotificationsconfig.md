# SlackNotificationsConfig

```
Configuration for Slack notifications.
```
  * **channel**: The Slack channel or user to send notifications to. Must start with # for channels or @ for users. (  Type: `str` )

  * **message_template**: Template for the message to be sent. Can include variables like env.BUILD_URL, env.JOB_NAME, etc. (  Type: `str` )

  * **pre_build_step**: Configuration for the notifications sent during the pre-build step phase. (  Type: `SlackNotificationPreBuildStepEventConfig` )
    * **simple_message**: Configuration for simple message notifications. (  Type: `SlackNotificationSimpleMessageConfig` )
      * **enabled**: Whether to send a simple text message. (  Type: `bool` Default: `True` )

      * **color**: Color for the notification in slack. (  Type: `Optional[str]` Default: `None` )

      * **channel_override**: Channel override for this message. (  Type: `str` Default: `` )

      * **message**: The message to send. (  Type: `str` Default: `` )


    * **blocks_message**: Configuration for blocks message notifications. (  Type: `SlackNotificationBlocksMessageConfig` )
      * **enabled**: Whether to send a blocks message. (  Type: `bool` Default: `False` )

      * **color**: Color for the notification in slack. (  Type: `Optional[str]` Default: `None` )

      * **channel_override**: Channel override for this message. (  Type: `str` Default: `` )

      * **blocks**: The blocks to send. (  Type: `str` Default: `` )



  * **on_success**: Configuration for the notifications sent during the on-sucess step phase. (  Type: `SlackNotificationOnSuccessEventConfig` )
    * **simple_message**: Configuration for simple message notifications. (  Type: `SlackNotificationSimpleMessageConfig` )
      * **enabled**: Whether to send a simple text message. (  Type: `bool` Default: `True` )

      * **color**: Color for the notification in slack. (  Type: `Optional[str]` Default: `None` )

      * **channel_override**: Channel override for this message. (  Type: `str` Default: `` )

      * **message**: The message to send. (  Type: `str` Default: `` )


    * **blocks_message**: Configuration for blocks message notifications. (  Type: `SlackNotificationBlocksMessageConfig` )
      * **enabled**: Whether to send a blocks message. (  Type: `bool` Default: `False` )

      * **color**: Color for the notification in slack. (  Type: `Optional[str]` Default: `None` )

      * **channel_override**: Channel override for this message. (  Type: `str` Default: `` )

      * **blocks**: The blocks to send. (  Type: `str` Default: `` )



  * **on_failure**: Configuration for the notifications sent during the on-failure step phase. (  Type: `SlackNotificationOnFailureEventConfig` )
    * **simple_message**: Configuration for simple message notifications. (  Type: `SlackNotificationSimpleMessageConfig` )
      * **enabled**: Whether to send a simple text message. (  Type: `bool` Default: `True` )

      * **color**: Color for the notification in slack. (  Type: `Optional[str]` Default: `None` )

      * **channel_override**: Channel override for this message. (  Type: `str` Default: `` )

      * **message**: The message to send. (  Type: `str` Default: `` )


    * **blocks_message**: Configuration for blocks message notifications. (  Type: `SlackNotificationBlocksMessageConfig` )
      * **enabled**: Whether to send a blocks message. (  Type: `bool` Default: `False` )

      * **color**: Color for the notification in slack. (  Type: `Optional[str]` Default: `None` )

      * **channel_override**: Channel override for this message. (  Type: `str` Default: `` )

      * **blocks**: The blocks to send. (  Type: `str` Default: `` )



  * **on_unstable**: Configuration for the notifications sent during the on-unstable step phase. (  Type: `SlackNotificationOnUnstableEventConfig` )
    * **simple_message**: Configuration for simple message notifications. (  Type: `SlackNotificationSimpleMessageConfig` )
      * **enabled**: Whether to send a simple text message. (  Type: `bool` Default: `True` )

      * **color**: Color for the notification in slack. (  Type: `Optional[str]` Default: `None` )

      * **channel_override**: Channel override for this message. (  Type: `str` Default: `` )

      * **message**: The message to send. (  Type: `str` Default: `` )


    * **blocks_message**: Configuration for blocks message notifications. (  Type: `SlackNotificationBlocksMessageConfig` )
      * **enabled**: Whether to send a blocks message. (  Type: `bool` Default: `False` )

      * **color**: Color for the notification in slack. (  Type: `Optional[str]` Default: `None` )

      * **channel_override**: Channel override for this message. (  Type: `str` Default: `` )

      * **blocks**: The blocks to send. (  Type: `str` Default: `` )



  * **on_exception**: Configuration for the notifications sent during the on-exception step phase. (  Type: `SlackNotificationOnExceptionEventConfig` )
    * **simple_message**: Configuration for simple message notifications. (  Type: `SlackNotificationSimpleMessageConfig` )
      * **enabled**: Whether to send a simple text message. (  Type: `bool` Default: `True` )

      * **color**: Color for the notification in slack. (  Type: `Optional[str]` Default: `None` )

      * **channel_override**: Channel override for this message. (  Type: `str` Default: `` )

      * **message**: The message to send. (  Type: `str` Default: `` )


    * **blocks_message**: Configuration for blocks message notifications. (  Type: `SlackNotificationBlocksMessageConfig` )
      * **enabled**: Whether to send a blocks message. (  Type: `bool` Default: `False` )

      * **color**: Color for the notification in slack. (  Type: `Optional[str]` Default: `None` )

      * **channel_override**: Channel override for this message. (  Type: `str` Default: `` )

      * **blocks**: The blocks to send. (  Type: `str` Default: `` )



  * **webhook_credential_id**: The Jenkins credentials ID for the Slack webhook. (  Type: `Optional[str]` Default: `None` )

[Back to main page](index.md)