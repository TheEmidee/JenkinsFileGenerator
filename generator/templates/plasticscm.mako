<%namespace name="groovy" module="generator.utils.groovy"/>

<%def name="additional_functions()">
def checkout() {
    cm(
    % if feature_config.checkout.shelveset or feature_config.checkout.label:
        % if feature_config.checkout.shelveset:
        shelveset: '${feature_config.checkout.shelveset}',
        % else:
        label: '${feature_config.checkout.label}',
        % endif
    % else:
        branch: '${feature_config.checkout.branch}',
        % if feature_config.checkout.changeset:
        changeset: '${feature_config.checkout.changeset}',
        % endif
    % endif
        changelog: '${feature_config.checkout.changelog}',
        poll: '${feature_config.checkout.poll}',
        repository: '${feature_config.checkout.remote_config.repository}',
        server: '${feature_config.checkout.remote_config.server}',
        cleanup: '${feature_config.checkout.cleanup}',
    % if feature_config.checkout.directory:
        directory: '${feature_config.checkout.directory}',
    % endif
    % if feature_config.checkout.credentials_config:
        workingMode: '${feature_config.checkout.credentials_config.working_mode}',
        credentialsId: '${feature_config.checkout.credentials_config.credentials_id}',
    % endif
    )
}
</%def>