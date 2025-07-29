<%namespace name="utils" file="utils.mako"/>

<%def name="post_build_steps()">
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
                            directory_path = "${feature_config.rotate_archives.directory_path}",
                            keep_count = "${feature_config.rotate_archives.keep_count}",
                            output_file = "${feature_config.rotate_archives.output_file_name}"
                        }
                """
            }
            % endif

            % if feature_config.upload_archives.enabled:
            stage ( "Upload Archives" ) {
                <%text>
                pwsh """
                    ."PyScripts/Tools/PyScript.ps1" `
                        -moduleName "uepyscripts.tools.archives.upload_archives" `
                        -arguments @{ 
                            directory_path = "${BUILD_TAG}"
                        }
                """
                </%text>
            }
            % endif
        }
    }
}
% endif
</%def>