## templates/base_jenkinsfile.mako
## Base Jenkinsfile template that combines all feature outputs

// THIS FILE HAS BEEN AUTO-GENERATED USING JenkinsFileGenerator - https://github.com/TheEmidee/JenkinsFileGenerator
// Version : ${global_values['generator_version']}
// Pipeline name : ${full_config.pipeline_name}
// Source YAML file : ${global_values['source_yaml_file']}
// Blackboard Data : ${global_values['blackboard_data']}

${libraries}

${imports}

properties([
${properties}
])

${pre_pipeline_steps}

try {
    ${build_steps}
    ${post_build_steps}

    if ( currentBuild.result == 'UNSTABLE' ) {
        ${on_build_unstable}
    } else if ( currentBuild.result == 'FAILURE' ) {
        ${on_build_failure}
    } else {
        ${on_build_success}
    }
} catch ( Exception e ) {
    ${on_exception_thrown}
    throw e
} finally {
    ${on_finally}
}

${additional_functions}