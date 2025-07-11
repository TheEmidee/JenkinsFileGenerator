<%namespace name="utils" file="utils.mako"/>

<%def name="build_steps()">
${feature_config._accumulator['jenkins_jobs_output']}
</%def>

<%def name="on_finally()">
% if feature_config.cleanup_after_build.enabled:
cleanup()
% endif
</%def>

<%def name="additional_functions()">
def runBuildGraph( group_name, task_names, platform, properties ) {
    node_name = "${full_config.jenkins.default_node_names} && <%text>${platform}</%text>"

    % if feature_config.buildgraph.node_name_filters is not None :
    <%
    items = [f"'{key}' : '{value}'" for key, value in feature_config.buildgraph.node_name_filters.items()]
    items = ", ".join(items)
    %>

    def node_name_filters = [ ${items} ]

    if ( !node_name_filters.isEmpty() ) {
        def node_name_filter = node_name_filters.get( group_name, "" )

        if ( node_name_filter?.trim() ) {
            node_name += "&& <%text>${node_name_filter}</%text>"
        }
    }
    % endif

    node( node_name ) {
        ${utils.initialize_env()}
        skipDefaultCheckout()
        ${utils.get_workspace()}
        {
            customCheckout()

            task_names.each { String task_name ->
                stage( task_name ) {
                    fileOperations( 
                        [ 
                            fileDeleteOperation( excludes: '', includes: 'Saved\\Jenkins\\*.txt' ),
                            fileDeleteOperation( excludes: '', includes: 'Saved\\Logs\\*.*' )
                        ] 
                    )

                    // This should not be added automatically
                    log.info "Net Use"
                    pwsh script: "Scripts/Project/CI/CI_NetUse.ps1"

                    <%text>log.info "Execute Buildgraph : ${task_name}"</%text>
                    <%text>pwsh script: "Scripts/Project/CI/CI_RunBuildGraph.ps1 \"${task_name}\" \"${BUILD_TAG}\" \"${properties}\""</%text>

                    % if feature_config.buildgraph.post_tasks.enabled:
                    postBuildGraphTasks( task_name )
                    % endif
                }
            }
        }
    }
}

% if feature_config.cleanup_after_build.enabled:
def cleanup( Boolean delete_versions_folder = false ) {
    <% 
    nodes = full_config.jenkins.default_node_names

    if feature_config.cleanup_after_build.additional_node_name.strip():
        nodes += " && " + feature_config.cleanup_after_build.additional_node_name.strip()
    %>    
    node( "${nodes}" ) {
        ${utils.initialize_env()}

        skipDefaultCheckout()

        ${utils.get_workspace()}
        {
            stage ( "Cleanup" ) {
                
                def str_value = String.valueOf( delete_versions_folder )
                
                // \044 is the octal representation of $
                // :TODO:
                ## pwsh script: "Scripts/Project/CI/CI_Cleanup.ps1 -BuildTag \"${BUILD_TAG}\" -DeleteVersionsFolder \044${str_value}"
            }
        }
    }
}
% endif

% if feature_config.buildgraph.post_tasks.enabled:
def postBuildGraphTasks( String task_name ) {
    def warnings_files = findFiles glob: 'Saved\\Jenkins\\*.txt'

    <%text>def record_issues_id = "BuildGraph_${task_name}".replaceAll("\\s+", "_");</%text>

    if ( task_name.contains( "Compile" ) ) {
        recordIssues enabledForFailure: true, failOnError: true, qualityGates: [[threshold: 1, type: 'TOTAL', unstable: false], [threshold: 1, type: 'TOTAL_ERROR', unstable: false]], tools: [ msBuild( id: record_issues_id, name: record_issues_id, pattern: 'Saved/Logs/Compile_*.log' ) ]
    } else if ( task_name.contains( "Static Analysis" ) ) {
        recordIssues enabledForFailure: true, failOnError: true, qualityGates: [[threshold: 1, type: 'TOTAL', unstable: false], [threshold: 1, type: 'TOTAL_ERROR', unstable: false]], tools: [ msBuild( id: record_issues_id, name: record_issues_id, pattern: 'Saved/Logs/StaticAnalysis_*.log' ) ]
    }

    if ( warnings_files.length > 0 ) {
        recordIssues enabledForFailure: true, failOnError: true, qualityGates: [[threshold: 1, type: 'TOTAL', unstable: false], [threshold: 1, type: 'TOTAL_ERROR', unstable: false]], tools: [groovyScript(id: record_issues_id, name: record_issues_id, parserId: 'UE_BuildgraphWarnings', pattern: 'Saved/Jenkins/*.txt')]
        % if feature_config.buildgraph.post_tasks.archive_artifacts:
        archiveArtifacts artifacts: 'Saved\\Jenkins\\*.txt', followSymlinks: false
        % endif
    }

    if ( fileExists ( 'Saved\\Tests\\Logs\\FunctionalTestsResults.xml' ) ) {
        junit testResults: "Saved\\Tests\\Logs\\FunctionalTestsResults.xml"
        % if feature_config.buildgraph.post_tasks.archive_artifacts:
        archiveArtifacts artifacts: 'Saved\\Tests\\Logs\\*.xml', followSymlinks: false
        % endif
    }
    
    % if feature_config.buildgraph.post_tasks.archive_artifacts:
    archiveArtifacts artifacts: 'Saved\\Logs\\*.log', followSymlinks: false, allowEmptyArchive: true
    % endif
}
% endif
</%def>