<%def name="pre_build_steps()">
def properties = "-set:Skip_Test_EditorBoot=True -set:Skip_Test_TargetBoot=True -set:Skip_Validation_CompileAllBlueprints=True -set:Skip_Validation_StaticAnalysis=True "


jobs = [:]
jobs[ "Compile MyGameEditor Win64" ] = {
    runBuildGraph( 
        "Compile MyGameEditor Win64", 
        [ 
            "MyGame Compile Editor Win64" 
        ],
        "Win64",
        properties 
        )
    }

jobs.failFast = true
parallel jobs
</%def>

<%def name="on_finally()">
% if feature_config.cleanup_after_build:
cleanup()
% endif
</%def>

<%def name="additional_functions()">
% if feature_config.cleanup_after_build:
def cleanup( Boolean delete_versions_folder = false ) {
    node( "UE_5.5 && Win64" ) {
        initializeEnvironment( this, "MyGame" )

        skipDefaultCheckout()

        ws( getWorkspace( this, "UE_5.5" ) ) {
            stage ( "Cleanup" ) {
                
                def str_value = String.valueOf( delete_versions_folder )
                
                // \044 is the octal representation of $
                pwsh script: "Scripts/Project/CI/CI_Cleanup.ps1 -BuildTag \"${BUILD_TAG}\" -DeleteVersionsFolder \044${str_value}"
            }
        }
    }
}
% endif

def runBuildGraph( group_name, task_names, platform, properties ) {
    node_name = "UE_5.5  && ${platform}"

    def node_name_filters = [ 'MyGame Editor Win64 Test=BootTest' : '!Builder6-TR', 'MyGame Win64 Development BootTest' : '!Builder6-TR', 'MyGame Editor Win64 Test=UE.EditorAutomation' : '!Builder6-TR', ]

    if ( !node_name_filters.isEmpty() ) {
        def node_name_filter = node_name_filters.get( group_name, "" )

        if ( node_name_filter?.trim() ) {
            node_name += "&& ${node_name_filter}"
        }
    }

    node( node_name ) {
        initializeEnvironment( this, "MyGame" )
        
        skipDefaultCheckout()

        ws( getWorkspace( this, "UE_5.5" ) ) {
            customCheckout()

            //checkLocalBuildGraphFolder()

            task_names.each { String task_name ->
                stage( task_name ) {
                    fileOperations( 
                        [ 
                            fileDeleteOperation( excludes: '', includes: 'Saved\\Jenkins\\*.txt' ),
                            fileDeleteOperation( excludes: '', includes: 'Saved\\Logs\\*.*' )
                        ] 
                    )

                    log.info "Net Use"
                    pwsh script: "Scripts/Project/CI/CI_NetUse.ps1"

                    log.info "Execute Buildgraph : ${task_name}"
                    pwsh script: "Scripts/Project/CI/CI_RunBuildGraph.ps1 \"${task_name}\" \"${BUILD_TAG}\" \"${properties}\""

                    postBuildGraphTasks( task_name )
                }
            }
        }
    }
}

def postBuildGraphTasks( String task_name ) {
    def warnings_files = findFiles glob: 'Saved\\Jenkins\\*.txt'

    def record_issues_id = "BuildGraph_${task_name}".replaceAll("\\s+", "_");

    if ( task_name.contains( "Compile" ) ) {
        recordIssues enabledForFailure: true, failOnError: true, qualityGates: [[threshold: 1, type: 'TOTAL', unstable: false], [threshold: 1, type: 'TOTAL_ERROR', unstable: false]], tools: [ msBuild( id: record_issues_id, name: record_issues_id, pattern: 'Saved/Logs/Compile_*.log' ) ]
    } else if ( task_name.contains( "Static Analysis" ) ) {
        recordIssues enabledForFailure: true, failOnError: true, qualityGates: [[threshold: 1, type: 'TOTAL', unstable: false], [threshold: 1, type: 'TOTAL_ERROR', unstable: false]], tools: [ msBuild( id: record_issues_id, name: record_issues_id, pattern: 'Saved/Logs/StaticAnalysis_*.log' ) ]
    }

    if ( warnings_files.length > 0 ) {
        recordIssues enabledForFailure: true, failOnError: true, qualityGates: [[threshold: 1, type: 'TOTAL', unstable: false], [threshold: 1, type: 'TOTAL_ERROR', unstable: false]], tools: [groovyScript(id: record_issues_id, name: record_issues_id, parserId: 'UE_BuildgraphWarnings', pattern: 'Saved/Jenkins/*.txt')]
        archiveArtifacts artifacts: 'Saved\\Jenkins\\*.txt', followSymlinks: false
    }

    if ( fileExists ( 'Saved\\Tests\\Logs\\FunctionalTestsResults.xml' ) ) {
        junit testResults: "Saved\\Tests\\Logs\\FunctionalTestsResults.xml"
        archiveArtifacts artifacts: 'Saved\\Tests\\Logs\\*.xml', followSymlinks: false
    }
    
    archiveArtifacts artifacts: 'Saved\\Logs\\*.log', followSymlinks: false, allowEmptyArchive: true
}
</%def>