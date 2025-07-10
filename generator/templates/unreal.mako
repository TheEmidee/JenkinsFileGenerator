<%def name="build_steps()">
${feature_config._accumulator['jenkins_jobs_output']}
</%def>

<%def name="on_finally()">
% if feature_config.cleanup_after_build.enabled:
cleanup()
% endif
</%def>

<%def name="additional_functions()">
% if feature_config.cleanup_after_build.enabled:
def cleanup( Boolean delete_versions_folder = false ) {
    node( "UE_5.5 && Win64" ) {
        initializeEnvironment( this, "MyGame" )

        skipDefaultCheckout()

        ws( getWorkspace( this, "UE_5.5" ) ) {
            stage ( "Cleanup" ) {
                
                def str_value = String.valueOf( delete_versions_folder )
                
                // \044 is the octal representation of $
                ## pwsh script: "Scripts/Project/CI/CI_Cleanup.ps1 -BuildTag \"${BUILD_TAG}\" -DeleteVersionsFolder \044${str_value}"
            }
        }
    }
}
% endif
</%def>