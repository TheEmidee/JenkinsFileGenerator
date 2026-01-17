<%def name="get_slack_channel(message_config, type='SlackNotificationMessageConfig')"><%
channel_override = message_config.channel_override.strip()
channel = (", " + channel_override) if channel_override and channel_override != feature_config.channel else ""
%>${channel}</%def>

<%def name="try_send_message(event, type='SlackNotificationEventConfig')">
    
    % if event.simple_message.enabled:
        sendMessageToSlack( "${event.simple_message.message}", "${event.simple_message.color}" ${get_slack_channel(event.simple_message).strip()} )
    % endif
    % if event.blocks_message.enabled:
        sendBlocksToSlack( [], "${event.blocks_message.color}" ${get_slack_channel(event.blocks_message).strip()} )
    % endif
</%def>

<%def name="libraries()">
@Library('slack-notifier@master')
</%def>

<%def name="build_steps()">
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
    slackSend( channel: channel, color: color, message: message + "${feature_config.message_template}" )
}
% endif

% if feature_config._accumulator.get("generate_send_blocks"):
def sendBlocksToSlack( blocks, String color, String channel = "${feature_config.channel}" ) {
    slackSend( channel: channel, color: color, blocks: blocks )
}
% endif
</%def>