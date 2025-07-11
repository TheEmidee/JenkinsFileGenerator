// Helper defs used accross multiple mako files

<%def name="initialize_env()">
initializeEnvironment( this, "${full_config.project.name}" )
</%def>

<%def name="get_workspace()">
<%
suffix = ''

if full_config.jenkins.workspace_suffix is not None:
    suffix = f', "{full_config.jenkins.workspace_suffix}"'
%>
ws( getWorkspace( this ${suffix} ) )
</%def>

// End of helper defs used accross multiple mako files

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

${initialize_env()}
</%def>