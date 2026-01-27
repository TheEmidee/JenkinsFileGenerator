<%def name="additional_functions()">
def activatePythonEnvironment() {
    pwsh "${feature_config.venv_activation_script_path}"
}

def executePythonScript(String scriptName, String arguments) {
    pwsh "${feature_config.venv_folder}Scripts/<%text>${scriptName}.exe ${arguments}</%text>"
}
</%def>