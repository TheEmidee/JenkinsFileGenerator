def warnings_files = findFiles glob: 'Saved\\Jenkins\\*.txt'

<%text>def record_issues_id = "BuildGraph_${taskName}".replaceAll('\\s+', '_');</%text>
def quality_gates = [[threshold: 1, type: 'TOTAL', unstable: false], [threshold: 1, type: 'TOTAL_ERROR', unstable: false]]

archiveArtifacts artifacts: 'Saved\\Logs\\*.log', followSymlinks: false, allowEmptyArchive: true