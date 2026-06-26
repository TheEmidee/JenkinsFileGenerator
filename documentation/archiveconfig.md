# ArchiveConfig

```
Archive feature for the Jenkins File Generator.
This feature allows to archive the artifacts or build products created by the jenkins pipeline.
It also allows to upload the archives to an S3 bucket.
It requires the python feature to work, and that you have in the requirements of your python folder in the project
a reference to the package GameDevTools.

Both actions have the same behavior:
1. The local folder will be copied over to the shared folder / s3 bucket with the current date
2. If a directory with the same name already exists, an incremental suffix will be added (_01, _02, etc...)
3. Only the specified number of most recent directories in the parent folder will be kept, older ones will be deleted.
4. Optionally, a slack notification can be sent on completion of the action.
```
  * **additional_node_name**: Additional jenkins node tags to use if you want the archiving tasks to be executed on specific nodes. (  Type: `Optional[str]` Default: `None` )

  * **rotate_archives**: Configuration for rotating archives (  (Required) Type: `RotateArchivesConfig` )
    * **enabled**: Enable or disable the action of rotating the archives (  Type: `bool` Default: `False` )

    * **source_directory**: Path to the source directory where to move the files from (  (Required) Type: `<class 'pathlib.Path'>` )

    * **destination_directory**: Path to the destination directory where to move the files to (in a new folder based on the current date (  (Required) Type: `<class 'pathlib.Path'>` )

    * **keep_count**: Number of directories to keep in the parent folder after directory_path has been renamed (  Type: `int` Default: `10` )

    * **folder_output_file_name**: Optional path to text file where the new directory name will be written to be re-used by other tasks (  Type: `Optional[pathlib.Path]` Default: `None` )

    * **slack**: Slack configuration (  Type: `Optional[features.archive.SlackNotificationConfig]` Default: `None` )
      * **enabled**: Enable or disable Slack notifications (  Type: `bool` Default: `False` )

      * **channel**: Slack channel to send notifications to (  Type: `str` Default: `` )

      * **message_template**: Template for the notification message (  Type: `str` Default: `` )



  * **upload_archives**: Configuration for uploading archives (  (Required) Type: `UploadArchivesConfig` )
    * **enabled**: Enable or disable the action of uploading the archives (  Type: `bool` Default: `False` )

    * **local_folder**: Path to the local folder containing the archives to upload. Optional. If you're using rotate_archives, jenkins will set the local folder path with the contents of output_file. (  Type: `Optional[pathlib.Path]` Default: `None` )

    * **bucket_name**: Name of the S3 bucket to upload the archives to (  Type: `str` Default: `` )

    * **region**: AWS region where the S3 bucket is located (  Type: `str` Default: `` )

    * **access_key**: Access key for AWS S3 authentication (  Type: `str` Default: `` )

    * **secret_key**: Secret key for AWS S3 authentication (  Type: `str` Default: `` )

    * **destination_folder**: Destination folder in the S3 bucket where the archives will be uploaded (  Type: `str` Default: `` )

    * **keep_count**: Number of archives to keep in the S3 bucket. If lower than 1, all archives will be kept. (  Type: `int` Default: `-1` )

    * **output_file_name**: Optional path to text file where the download URLs of uploaded archives will be written (  Type: `Optional[pathlib.Path]` Default: `None` )

    * **slack**: Slack configuration (  Type: `Optional[features.archive.SlackNotificationConfig]` Default: `None` )
      * **enabled**: Enable or disable Slack notifications (  Type: `bool` Default: `False` )

      * **channel**: Slack channel to send notifications to (  Type: `str` Default: `` )

      * **message_template**: Template for the notification message (  Type: `str` Default: `` )



[Back to main page](index.md)