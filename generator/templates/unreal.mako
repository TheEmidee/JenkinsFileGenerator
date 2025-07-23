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
def executeJobsInParallel(List jobGroup, String properties) {
    def parallelJobs = [:]
    
    jobGroup.each { jobMap ->
        jobMap.each { jobName, jobConfig ->
            parallelJobs[jobName] = {
                runBuildGraph(
                    jobName,
                    jobConfig.tasks,
                    jobConfig.platform,
                    properties
                )
            }
        }
    }
    
    parallelJobs.failFast = true
    parallel parallelJobs
}

def runBuildGraph( groupName, taskNames, platform, properties ) {
    def nodeName = "${full_config.jenkins.default_node_names} && <%text>${platform}</%text>"

    % if feature_config.buildgraph.node_name_filters is not None :
    <%
    items = [f"'{key}' : '{value}'" for key, value in feature_config.buildgraph.node_name_filters.items()]
    items = ", ".join(items)
    %>

    def nodeNameFilters = [ ${items} ]

    if ( !nodeNameFilters.isEmpty() ) {
        def node_name_filter = nodeNameFilters.get( groupName, "" )

        if ( node_name_filter?.trim() ) {
            nodeName += "&& <%text>${node_name_filter}</%text>"
        }
    }
    % endif

    node( nodeName ) {
        ${utils.initialize_env()}
        
        skipDefaultCheckout()
        
        ${utils.get_workspace()}
        {
            gitCheckout()

            taskNames.each { String taskName ->
                stage( taskName ) {
                    preBuildGraphTasks()

                    % for pre_task in feature_config.buildgraph.pre_tasks:
                    ${pre_task}
                    % endfor

                    <%text>
                    pwsh """
                        ."PyScripts/Tools/PyScript.ps1" `
                            -moduleName "uepyscripts.tools.ci.buildgraph" `
                            -arguments @{ 
                                target = "${taskName}" 
                                build_tag = "${BUILD_TAG}"
                                string_arguments = "${properties}"
                            }
                    """
                    </%text>

                    % if feature_config.buildgraph.post_tasks.enabled:
                    postBuildGraphTasks( taskName )
                    % endif
                }
            }
        }
    }
}

def preBuildGraphTasks() {
    fileOperations( 
        [ 
            fileDeleteOperation( excludes: '', includes: 'Saved\\Jenkins\\*.txt' ),
            fileDeleteOperation( excludes: '', includes: 'Saved\\Logs\\*.*' )
        ] 
    )
}

% if feature_config.cleanup_after_build.enabled:
def cleanup() {
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
            gitCheckout()

            stage ( "Cleanup" ) {
                <%text>
                pwsh """
                    ."PyScripts/Tools/PyScript.ps1" `
                        -moduleName "uepyscripts.tools.ci.cleanup" `
                        -arguments @{ 
                            build_tag = "${BUILD_TAG}"
                        }
                """
                </%text>
            }
        }
    }
}
% endif

% if feature_config.buildgraph.post_tasks.enabled:
def postBuildGraphTasks( String taskName ) {
    def warnings_files = findFiles glob: 'Saved\\Jenkins\\*.txt'

    <%text>def record_issues_id = "BuildGraph_${taskName}".replaceAll('\\s+', '_');</%text>
    def quality_gates = [[threshold: 1, type: 'TOTAL', unstable: false], [threshold: 1, type: 'TOTAL_ERROR', unstable: false]]

    if ( taskName.contains( "Compile" ) ) {
        recordIssues enabledForFailure: true, failOnError: true, qualityGates : quality_gates, tools: [ msBuild( id: record_issues_id, name: record_issues_id, pattern: 'Saved/Logs/Compile_*.log' ) ]
    } else if ( taskName.contains( "Static Analysis" ) ) {
        recordIssues enabledForFailure: true, failOnError: true, qualityGates : quality_gates, tools: [ msBuild( id: record_issues_id, name: record_issues_id, pattern: 'Saved/Logs/StaticAnalysis_*.log' ) ]
    }

    if ( warnings_files.length > 0 ) {
        recordIssues enabledForFailure: true, failOnError: true, qualityGates : quality_gates, tools: [groovyScript(id: record_issues_id, name: record_issues_id, parserId: 'UE_BuildgraphWarnings', pattern: 'Saved/Jenkins/*.txt')]
        % if feature_config.buildgraph.post_tasks.archive_artifacts:
        archiveArtifacts artifacts: 'Saved\\Jenkins\\*.txt', followSymlinks: false
        % endif
    }

    def functional_tests_results_path = 'Saved\\Tests\\Logs\\FunctionalTestsResults.xml'
    if ( fileExists( functional_tests_results_path ) ) {
        junit testResults: functional_tests_results_path
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