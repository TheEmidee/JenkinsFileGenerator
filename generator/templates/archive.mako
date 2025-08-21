<%namespace name="utils" file="utils.mako"/>

<%def name="build_steps()">
% if feature_config.rotate_archives.enabled or feature_config.upload_archives.enabled:
archivePackages()
% endif
</%def>

<%def name="additional_functions()">
% if feature_config.rotate_archives.enabled or feature_config.upload_archives.enabled:
def archivePackages() {
    <% 
    nodes = full_config.jenkins.default_node_names
    if feature_config.additional_node_name and feature_config.additional_node_name.strip():
        nodes += " && " + feature_config.additional_node_name.strip()
    %>

    node( "${nodes}" ) {
        ${utils.initialize_env()}

        skipDefaultCheckout()

        ${utils.get_workspace()} 
        {
            checkout()

            % if feature_config.rotate_archives.enabled:
            stage ( "Rotate Archives" ) {
                pwsh """
                    ."PyScripts/Tools/PyScript.ps1" `
                        -moduleName "uepyscripts.tools.archives.rotate_archives" `
                        -arguments @{ 
                            directory_path = "${feature_config.rotate_archives.directory_path.as_posix()}"
                            keep_count = "${feature_config.rotate_archives.keep_count}"
                            folder_output_file_name = "${feature_config.rotate_archives.folder_output_file_name.as_posix()}"
                        }
                """

                % if feature_config.rotate_archives.slack and feature_config.rotate_archives.slack.enabled:
                slackSend( channel: "${feature_config.rotate_archives.slack.channel}", message: "${feature_config.rotate_archives.slack.message_template}" )
                % endif
            }
            % endif

            % if feature_config.upload_archives.enabled:

            % if feature_config.rotate_archives.enabled:
            def file = readFile "${feature_config.rotate_archives.folder_output_file_name.as_posix()}"
            % else:
            def file = "${feature_config.upload_archives.local_folder}"
            % endif 

            stage ( "Upload Archives" ) {
                pwsh """
                    ."PyScripts/Tools/PyScript.ps1" `
                        -moduleName "uepyscripts.tools.archives.upload_archives" `
                        -arguments @{ 
                            <%text>local_folder = "${file}"</%text>
                            bucket_name = "${feature_config.upload_archives.bucket_name}"
                            region = "${feature_config.upload_archives.region}"
                            access_key = "${feature_config.upload_archives.access_key}"
                            secret_key = "${feature_config.upload_archives.secret_key}"
                            destination_folder = "${feature_config.upload_archives.destination_folder}"
                            keep_count = "${feature_config.upload_archives.keep_count}"
                            output_file = "${feature_config.upload_archives.output_file_name.as_posix()}"
                        }
                """

                % if feature_config.upload_archives.slack and feature_config.upload_archives.slack.enabled:
                def uploaded_files = readFile "${feature_config.upload_archives.output_file_name.as_posix()}"
                def lines = uploaded_files.split('\n')

                if ( lines.size() > 0 ) {
                    def message = 'Uploaded builds:\n'

                    lines.each { String line ->
                        def parts = line.split(" : ", 2)
                        if (parts.size() == 2) {
                            def url = parts[0].trim()
                            def filename = parts[1].trim()
                            message += "${feature_config.upload_archives.slack.message_template}\n"
                        }
                    }

                    slackSend( channel: "${feature_config.upload_archives.slack.channel}", message: message )
                } else {
                    slackSend( channel: "${feature_config.upload_archives.slack.channel}", color: "danger", message: "No files were uploaded" )
                }

                % endif
            }
            % endif
        }
    }
}
% endif
</%def>