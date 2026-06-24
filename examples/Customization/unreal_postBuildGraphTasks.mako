def warnings_files = findFiles glob: 'Saved\\Jenkins\\*.txt'

def sanitizedTaskName = taskName.replaceAll('\\s+', '_')
<%text>def record_issues_id = "BuildGraph_${sanitizedTaskName}"</%text>
def quality_gates = [[threshold: 1, type: 'TOTAL', unstable: false], [threshold: 1, type: 'TOTAL_ERROR', unstable: false]]

if (fileExists('Saved/Logs/Log.txt')) {
    <%text>fileOperations([fileRenameOperation(destination: "Saved/Logs/${sanitizedTaskName}.log", source: 'Saved/Logs/Log.txt')])</%text>
}
if (fileExists('Saved/Logs/BuildCookRun/Log.txt')) {
    <%text>fileOperations([fileRenameOperation(destination: "Saved/Logs/${sanitizedTaskName}_BuildCookRun.log", source: 'Saved/Logs/BuildCookRun/Log.txt')])</%text>
}

recordIssues enabledForFailure: true, failOnError: true, qualityGates : quality_gates, tools: [ msBuild( id: record_issues_id, name: record_issues_id, pattern: 'Saved/Logs/*.log' ) ]

if ( ( taskName.contains( 'Compile' ) && !taskName.contains( 'Blueprints' ) ) || taskName.contains( 'Static Analysis' ) ) {
    recordIssues enabledForFailure: true, failOnError: true, qualityGates : quality_gates, tools: [ msBuild( id: record_issues_id, name: record_issues_id, pattern: 'Saved/Logs/*.log' ) ]
} else {
    recordIssues enabledForFailure: true, failOnError: true, qualityGates : quality_gates, tools: [groovyScript(id: record_issues_id, name: record_issues_id, parserId: 'UE_BuildgraphWarnings', pattern: 'Saved/Logs/*.log')]
}

def functional_tests_results_path = 'Saved\\Tests\\Logs\\FunctionalTestsResults.xml'
if ( fileExists( functional_tests_results_path ) ) {
    junit testResults: functional_tests_results_path
    archiveArtifacts artifacts: 'Saved\\Tests\\Logs\\*.xml', followSymlinks: false
}

archiveArtifacts artifacts: 'Saved\\Logs\\*.log', followSymlinks: false, allowEmptyArchive: true