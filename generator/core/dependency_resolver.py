from typing import List

from generator.core.base_feature import BaseFeature


class DependencyResolver:
    """Resolves feature dependencies using topological sorting."""

    @staticmethod
    def resolve_dependencies(features: List[BaseFeature]) -> List[BaseFeature]:
        """Sort features based on their dependencies using topological sort."""
        # Create dependency graph
        feature_map = {f.feature_name: f for f in features}
        in_degree = {f.feature_name: 0 for f in features}
        graph = {f.feature_name: [] for f in features}

        # Build the graph
        for feature in features:
            for dep in feature.dependencies:
                if dep not in feature_map:
                    raise ValueError(
                        f"Feature '{feature.feature_name}' depends on '{dep}', but '{dep}' is not available"
                    )
                graph[dep].append(feature.feature_name)
                in_degree[feature.feature_name] += 1

        # Topological sort using Kahn's algorithm
        queue = [name for name, degree in in_degree.items() if degree == 0]
        sorted_names = []

        while queue:
            current = queue.pop(0)
            sorted_names.append(current)

            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Check for circular dependencies
        if len(sorted_names) != len(features):
            remaining = [name for name, degree in in_degree.items() if degree > 0]
            raise ValueError(
                f"Circular dependency detected among features: {remaining}"
            )

        # Return features in dependency order
        return [feature_map[name] for name in sorted_names]
