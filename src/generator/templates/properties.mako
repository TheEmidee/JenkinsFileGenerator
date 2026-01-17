<%def name="properties()">
% for property in feature_config.items:
${property},
% endfor
</%def>