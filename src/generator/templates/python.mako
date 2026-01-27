<%def name="additional_functions()">
def activatePythonEnvironment() {
    pwsh "${feature_config.venv_activation_script_path}"
}

def executePythonScript(String scriptName, String arguments) {
    pwsh """
        . "Scripts/Python/.venv/Scripts/<%text>${scriptName}.exe" `
        ${arguments}</%text>
"""
}
</%def>