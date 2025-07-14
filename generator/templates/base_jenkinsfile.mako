## templates/base_jenkinsfile.mako
## Base Jenkinsfile template that combines all feature outputs

// THIS FILE HAS BEEN AUTO-GENERATED USING JenkinsFileGenerator
// Version : ${global_values['generator_version']}
// Pipeline name : ${full_config.pipeline_name}

${libraries}

${imports}

properties([
${properties}
])

${pre_pipeline_steps}

try {
    ${build_steps}

    if ( currentBuild.result == 'UNSTABLE' ) {
        ${on_build_unstable}
    } else if ( currentBuild.result == 'FAILURE' ) {
        ${on_build_failure}
    } else {
        ${on_build_success}
    }

    ${post_build_steps}
} catch ( Exception e ) {
    ${on_exception_thrown}
    throw e
} finally {
    ${on_finally}
}

${additional_functions}