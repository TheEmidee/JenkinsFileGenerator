"""Graph utility for managing dependencies and performing topological sorting."""

from collections import defaultdict, deque

def build_dependency_graph(groups: dict[str, list[str]], dependencies: dict[str, list[str]]) -> list[list[str]]:
    """
    Topologically sort groups based on inter-group job dependencies,
    returning batches of groups that can run in parallel.

    Args:
        groups: {"group_a": ["job_1", "job_2"], "group_b": ["job_3"], ...}
        dependencies: {"job_3": ["job_1", "job_2"], ...}  # job -> list of jobs it depends on

    Returns:
        List of batches, e.g. [["group_a"], ["group_b", "group_c"], ["group_d"]]
        Groups within the same batch can run in parallel.
    """
    # Build a reverse map: job -> its group
    job_to_group = {}
    for group, jobs in groups.items():
        for job in jobs:
            job_to_group[job] = group

    # Build group-level dependency edges
    # group_deps[A] = set of groups that A depends on
    group_deps: dict[str, set[str]] = {group: set() for group in groups}

    for job, dep_jobs in dependencies.items():
        dependent_group = job_to_group.get(job)
        if dependent_group is None:
            raise ValueError(f"Job '{job}' not found in any group")

        for dep_job in dep_jobs:
            dep_group = job_to_group.get(dep_job)
            if dep_group is None:
                raise ValueError(f"Dependency job '{dep_job}' not found in any group")

            # Only register cross-group dependencies
            if dep_group != dependent_group:
                group_deps[dependent_group].add(dep_group)

    # Kahn's algorithm — count in-degrees
    in_degree = {group: len(deps) for group, deps in group_deps.items()}

    # Build reverse edges: group -> groups that depend on it
    dependents: dict[str, set[str]] = defaultdict(set)
    for group, deps in group_deps.items():
        for dep in deps:
            dependents[dep].add(group)

    # Start with all groups that have no dependencies
    queue = deque(group for group, degree in in_degree.items() if degree == 0)
    result = []

    while queue:
        # All groups currently in the queue form a parallel batch
        batch = list(queue)
        queue.clear()
        result.append(batch)

        for group in batch:
            for dependent in dependents[group]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

    # Detect cycles
    if sum(len(b) for b in result) != len(groups):
        resolved = {g for batch in result for g in batch}
        unresolved = set(groups) - resolved
        raise ValueError(f"Cycle detected among groups: {unresolved}")

    return result