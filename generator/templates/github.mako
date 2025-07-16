<%def name="libraries()">
@Library('jenkins-github@develop')
</%def>

<%def name="pre_pipeline_steps()">
%if feature_config._accumulator.get("get_github_pr_infos") :

def deployment_environment = Environment.instance.DEPLOYMENT_ENVIRONMENT as DeploymentEnvironment

if ( deployment_environment == DeploymentEnvironment.PullRequest ) {
    def pull_request_infos = getGitHubPRInfos()

    % if feature_config._accumulator.get("update_job_description_from_pr") :
    updateJobDescriptionFromPR( pull_request_infos )
    % endif

    % if feature_config._accumulator.get("can_process_pull_request") :
    def ( can_process_build, message, build_result ) = canProcessPullRequest( pull_request_infos )

    if ( !can_process_build ) {
        log.info message
        currentBuild.result = build_result
        return
    }
    % endif
}

%endif
</%def>

<%def name="additional_functions()">
% if feature_config._accumulator.get("can_process_pull_request"):
def canProcessPullRequest( pull_request_infos ) {
    Boolean can_process_build = true
    String pr_title = ""
    String message = ""
    String build_result = ""

    if ( pull_request_infos != null ) {
        pr_title = pull_request_infos.title
    }

    def tokens = ${feature_config.pull_requests.filter.tokens}
    def foundToken = tokens.find { token -> pr_title.toLowerCase().contains(token.toLowerCase()) }

    if ( foundToken ) {
        can_process_build = false
        message = "${feature_config.pull_requests.filter.message}"
        build_result = 'NOT_BUILT'
    }

    return [ can_process_build, message, build_result ]
}
% endif

% if feature_config._accumulator.get("update_job_description_from_pr"):
def updateJobDescriptionFromPR( pull_request_infos ) {
    if ( pull_request_infos == null ) {
        return
    }

    def pr_body = pull_request_infos.body
    currentBuild.description = pr_body
}
% endif

% if feature_config._accumulator.get("get_github_pr_infos"):
def getGitHubPRInfos() {
    def pull_request_infos = null

    def deployment_environment = Environment.instance.DEPLOYMENT_ENVIRONMENT as DeploymentEnvironment

    if ( deployment_environment == DeploymentEnvironment.PullRequest ) {
        withCredentials( [ string( credentialsId: '${feature_config.credentials_id}', variable: 'GITHUB_ACCESS_TOKEN' ) ] ) {
            pull_request_infos = getGitHubCurrentPullRequestInfos( this, GITHUB_ACCESS_TOKEN, "${feature_config.owner}", "${feature_config.repository}" )
        }
    }

    return pull_request_infos
}
% endif
</%def>