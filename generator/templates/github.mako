<%def name="libraries()">
@Library('jenkins-github@develop')
</%def>

<%def name="pre_pipeline_steps()">
%if feature_config._accumulator.get("get_github_pr_infos") :

def deploymentEnvironment = Environment.instance.DEPLOYMENT_ENVIRONMENT as DeploymentEnvironment

if ( deploymentEnvironment == DeploymentEnvironment.PullRequest ) {
    def pullRequestInfos = getGitHubPullRequestInfos()

    % if feature_config._accumulator.get("update_job_description_from_pr") :
    updateJobDescriptionFromPullRequest( pullRequestInfos )
    % endif

    % if feature_config._accumulator.get("can_process_pull_request") :
    def ( canProcessBuild, message, buildResult ) = canProcessPullRequest( pullRequestInfos )

    if ( !canProcessBuild ) {
        log.info message
        currentBuild.result = buildResult
        return
    }
    % endif
}

%endif
</%def>

<%def name="additional_functions()">
% if feature_config._accumulator.get("can_process_pull_request"):
def canProcessPullRequest( pullRequestInfos ) {
    Boolean canProcessBuild = true
    String pullRtequestTitle = ""
    String message = ""
    String buildResult = ""

    if ( pullRequestInfos != null ) {
        pullRtequestTitle = pullRequestInfos.title
    }

    def tokens = ${feature_config.pull_requests.filter.tokens}
    def foundToken = tokens.find { token -> pullRtequestTitle.toLowerCase().contains(token.toLowerCase()) }

    if ( foundToken ) {
        canProcessBuild = false
        message = "${feature_config.pull_requests.filter.message}"
        buildResult = 'NOT_BUILT'
    }

    return [ canProcessBuild, message, buildResult ]
}
% endif

% if feature_config._accumulator.get("update_job_description_from_pr"):
def updateJobDescriptionFromPullRequest( pullRequestInfos ) {
    if ( pullRequestInfos == null ) {
        return
    }

    def pr_body = pullRequestInfos.body
    currentBuild.description = pr_body
}
% endif

% if feature_config._accumulator.get("get_github_pr_infos"):
def getGitHubPullRequestInfos() {
    def pullRequestInfos = null

    def deploymentEnvironment = Environment.instance.DEPLOYMENT_ENVIRONMENT as DeploymentEnvironment

    if ( deploymentEnvironment == DeploymentEnvironment.PullRequest ) {
        withCredentials( [ string( credentialsId: '${feature_config.credentials_id}', variable: 'GITHUB_ACCESS_TOKEN' ) ] ) {
            pullRequestInfos = getGitHubCurrentPullRequestInfos( this, GITHUB_ACCESS_TOKEN, "${feature_config.owner}", "${feature_config.repository}" )
        }
    }

    return pullRequestInfos
}
% endif
</%def>