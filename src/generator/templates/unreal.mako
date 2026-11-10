<%namespace name="utils" file="utils.mako"/>

<%!
def buildgraph_properties(buildgraph):
    """Arguments and -set: properties passed to ue-ci-run-buildgraph, one per line.
    The ` at the end of each line is important for the PowerShell call."""
    text = ""
    if buildgraph.arguments is not None:
        text += " `\n".join(buildgraph.arguments) + " `\n"
    if not buildgraph.use_parallel_jobs:
        text += "--no-single-node `\n"
    if buildgraph.properties is not None:
        text += " `\n".join(f"-set:{key}={value}" for key, value in buildgraph.properties.items()) + " `\n"
    return text
%>

<%def name="build_steps()">
% if feature_config.buildgraph.use_parallel_jobs:
    def buildgraph_job_groups = [
% for batch in buildgraph_plan.batches:
        [
    % for job_group in batch:
            [
                "${job_group.name}": [
                    tasks: [ ${", ".join(f'"{node_name}"' for node_name in job_group.node_names)} ],
                    platform: "${job_group.agent_type}"
                ],
            ],
    % endfor
        ],
% endfor
    ]

    buildgraph_job_groups.each { group ->
        executeJobsInParallel(group)
    }
% else:
runBuildGraph("${feature_config.buildgraph.target}")
% endif
</%def>

<%def name="on_finally()">
% if feature_config.cleanup_after_build and feature_config.cleanup_after_build.enabled:
cleanup()
% endif
</%def>

<%def name="additional_functions()">
% if feature_config.buildgraph.use_parallel_jobs:
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
            projectCheckout()

            % if global_values['customization'].get('unreal_postProjectCheckout'):
            <%include file="${global_values['customization']['unreal_postProjectCheckout']}"/>
            % endif

            taskNames.each { String taskName ->
                stage( taskName ) {
                    preBuildGraphTasks()

                    % for pre_task in feature_config.buildgraph.pre_tasks:
                    ${pre_task}
                    % endfor

                    def build_tag = getSanitizedBuildTag()

                    // It's important to NOT have an end of line before the first argument otherwise Jenkins will fail to execute the posh script
                    def properties = """<%text>--target="${taskName}" `
--build_tag="${build_tag}"</%text> `
${buildgraph_properties(feature_config.buildgraph)}
"""

                    executeAutomationScript( "ue-ci-run-buildgraph", properties )

                    postBuildGraphTasks( taskName )
                }
            }
        }
    }
}

% else:

def runBuildGraph( taskName ) {
    node( "${full_config.jenkins.default_node_names}" ) {
        ${utils.initialize_env()}
        
        skipDefaultCheckout()
        
        ${utils.get_workspace()}
        {
            projectCheckout()

            % if global_values['customization'].get('unreal_postProjectCheckout'):
            <%include file="${global_values['customization']['unreal_postProjectCheckout']}"/>
            % endif

            stage( taskName ) {
                preBuildGraphTasks()

                % for pre_task in feature_config.buildgraph.pre_tasks:
                ${pre_task}
                % endfor

                def build_tag = getSanitizedBuildTag()

                // It's important to NOT have an end of line before the first argument otherwise Jenkins will fail to execute the posh script
                def properties = """<%text>--target="${taskName}" `
--build_tag="${build_tag}"</%text> `
${buildgraph_properties(feature_config.buildgraph)}
"""

                executeAutomationScript( "ue-ci-run-buildgraph", properties )

                postBuildGraphTasks( taskName )
            }
        }
    }
}
% endif

def executeAutomationScript(String scriptName, String arguments) {
    % if feature_config.automation and feature_config.automation.logs_folder:
    def logFolder = "${feature_config.automation.logs_folder}"
    <%text>withEnv( ["uebp_LogFolder=${logFolder}"] ) {</%text>
    % endif
    executePythonScript(scriptName, arguments)
    % if feature_config.automation and feature_config.automation.logs_folder:
    }
    % endif
}

% if feature_config.cleanup_after_build and feature_config.cleanup_after_build.enabled:
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
                runSetupScript()

                def build_tag = getSanitizedBuildTag()
                executeAutomationScript( "ue-ci-cleanup", <%text>"--build_tag=${build_tag}"</%text> )
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
    runSetupScript()

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

def runSetupScript() {
    <%text>def setupJobIdFile = "${WORKSPACE}/Saved/JenkinsSetupScriptJobId.txt"</%text>
    def currentBuildTag = getSanitizedBuildTag()

    def shouldRunSetup = true

    if (fileExists(setupJobIdFile)) {
        def existingTag = readFile(setupJobIdFile).trim()
        if (existingTag == currentBuildTag) {
            <%text>echo "Setup already ran for build tag '${currentBuildTag}'. Skipping."</%text>
            shouldRunSetup = false
        }
    }

    if (shouldRunSetup) {
        <%text>echo "Running setup script for build tag '${currentBuildTag}'..."</%text>
        pwsh 'New-Item -ItemType Directory -Force -Path Saved'
        writeFile file: setupJobIdFile, text: currentBuildTag
        <%text>pwsh script: "${WORKSPACE}/Setup.ps1 -BuildMachine"</%text>
    }
}

def getSanitizedBuildTag() {
    return BUILD_TAG.replace(" ", "_")
}

% if global_values['customization'].get('unreal_additionalFunctions'):
<%include file="${global_values['customization']['unreal_additionalFunctions']}"/>
% endif

</%def>