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
def executeJobsInParallel(List jobGroup) {
    def parallelJobs = [:]
    
    jobGroup.each { jobMap ->
        jobMap.each { jobName, jobConfig ->
            parallelJobs[jobName] = {
                runBuildGraph(
                    jobName,
                    jobConfig.tasks,
                    jobConfig.platform
                )
            }
        }
    }
    
    parallelJobs.failFast = true
    parallel parallelJobs
}

def runBuildGraph( groupName, taskNames, platform ) {
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
            def scmVars = checkout()

            taskNames.each { String taskName ->
                stage( taskName ) {
                    preBuildGraphTasks()

                    % for pre_task in feature_config.buildgraph.pre_tasks:
                    ${pre_task}
                    % endfor

                    def build_tag = BUILD_TAG.replace(" ", "_")

                    def properties = """
<%text>--target="${taskName}" 
--build_tag="${build_tag}"</%text> 
${feature_config._accumulator['buildgraph_properties']}
"""

                    executePythonScript( "ue-ci-run-buildgraph", properties )

                    postBuildGraphTasks( taskName )
                }
            }
        }
    }
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
            projectCheckout()

            stage ( "Cleanup" ) {
                activatePythonEnvironment()

                executePythonScript( "ue-ci-cleanup", <%text>"--build_tag=${BUILD_TAG}"</%text> )
            }

            postCleanupTasks()
        }
    }
}
% endif

def postCleanupTasks() {
    % if global_values['customization'].get('unreal_postCleanupTasks'):
    <%include file="${global_values['customization']['unreal_postCleanupTasks']}"/>
    % endif
}

def preBuildGraphTasks() {
    activatePythonEnvironment()

    fileOperations( 
        [ 
            fileDeleteOperation( excludes: '', includes: 'Saved\\Jenkins\\*.txt' ),
            fileDeleteOperation( excludes: '', includes: 'Saved\\Logs\\*.*' )
        ] 
    )

    % if global_values['customization'].get('unreal_preBuildGraphTasks'):
    <%include file="${global_values['customization']['unreal_preBuildGraphTasks']}"/>
    % endif
}


def postBuildGraphTasks( String taskName ) {
    % if global_values['customization'].get('unreal_postBuildGraphTasks'):
    <%include file="${global_values['customization']['unreal_postBuildGraphTasks']}"/>
    % endif
}
</%def>