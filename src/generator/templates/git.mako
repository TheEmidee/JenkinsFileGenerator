<%namespace name="groovy" module="generator.utils.groovy"/>

<%def name="additional_functions()">
def projectCheckout() {
% for pre_task in feature_config.pre_checkout_tasks:
    ${pre_task}
% endfor

% if feature_config.retry_count > 1:
    retry(count: ${feature_config.retry_count}) {
% endif
    ${feature_config.checkout_code}
% if feature_config.retry_count > 1:
    }
% endif

}
</%def>