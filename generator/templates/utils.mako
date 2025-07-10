<%def name="libraries()">
@Library('jenkins-utils@master')
</%def>

<%def name="imports()">
import org.emidee.jenkins.DeploymentEnvironment
import org.emidee.jenkins.Environment
import groovy.transform.Field
</%def>

<%def name="pre_pipeline_steps()">
% if feature_config.abort_running_builds :
abortPreviousRunningBuilds()
% endif

initializeEnvironment( this, "${pipeline_name}" )

def deployment_environment = Environment.instance.DEPLOYMENT_ENVIRONMENT as DeploymentEnvironment
</%def>