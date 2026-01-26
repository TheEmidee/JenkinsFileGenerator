<%def name="additional_functions()">
def activatePythonEnvironment() {
    <%text>pwsh """
        ."</%text>${feature_config.venv_activation_script_path}<%text>"
    """
    </%text>
}

def executePythonScript(String scriptName, String arguments) {
    <%text>pwsh """
        ."</%text>${feature_config.venv_folder}<%text>Scripts/${scriptName}.exe ${arguments}"
    """
    </%text>
}
</%def>