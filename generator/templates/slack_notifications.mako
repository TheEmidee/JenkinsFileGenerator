<%def name="try_send_message(event, type='SlackNotificationEventConfig')">
    
    % if event.simple_message.enabled:
        <%
            channel = feature_config.channel
            if event.simple_message.channel_override.strip():
                channel = event.simple_message.channel_override.strip()
        %>
        
        sendMessageToSlack( channel: "${channel}", color: "${event.simple_message.color}", message: "${event.simple_message.message}" )
    % endif
    % if event.blocks_message.enabled:
        <%
            channel = feature_config.channel
            if event.blocks_message.channel_override.strip():
                channel = event.blocks_message.channel_override.strip()
        %>
        
        sendBlocksToSlack( channel: "${channel}", color: "${event.blocks_message.color}", blocks: [] )
    % endif
</%def>

<%def name="libraries()">
@Library('slack-notifier@master')
</%def>

<%def name="pre_build_steps()">
${try_send_message(event=feature_config.pre_build_step)}
</%def>

<%def name="on_build_failure()">
${try_send_message(event=feature_config.on_failure)}
</%def>

<%def name="on_build_unstable()">
${try_send_message(event=feature_config.on_unstable)}
</%def>

<%def name="on_build_success()">
${try_send_message(event=feature_config.on_success)}
</%def>

<%def name="on_exception_thrown()">
${try_send_message(event=feature_config.on_exception)}
</%def>

<%def name="additional_functions()">
% if feature_config._accumulator.get("generate_send_message"):
def sendMessageToSlack( String message, String color, String channel = "${feature_config.channel}" ) {
    slackSend( channel: channel, color: color, message: message )
}
% endif

% if feature_config._accumulator.get("generate_send_blocks"):
def sendBlocksToSlack( blocks, String color, String channel = "${feature_config.channel}" ) {
    slackSend( channel: channel, color: color, blocks: blocks )
}
% endif
</%def>