<%def name="additional_functions()">
def gitCheckout() {
% if feature_config.use_simple_checkout:
    checkout scm
% else:
    checkout([
        $class: 'GitSCM',
        branches: 
        [ 
            { 'name': '${feature_config.branch_name}' } 
        ],
        extensions: 
        [
        % for key, options in feature_config.extensions.items():
            <% should_emit = options.should_emit() %>
            [
                $class: '${options.get_class_name()}'${',' if should_emit else ''}
                % if should_emit:
                    % for k, v in options.dict().items():
                ${k}: ${utils.write_groovy_repr(v)}${',' if not loop.last else ''}
                    % endfor
                % endif
            ],
        % endfor
        ], 
        userRemoteConfigs: [
            [ credentialsId: '${feature_config.user_remote_config.credentials_id.id}', url: '${feature_config.user_remote_config.credentials_id.url}' ]
        ]
    ])
% endif
}
</%def>