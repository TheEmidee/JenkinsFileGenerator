from collections import defaultdict, deque

class Graph:
    def __init__(self):
        self.graph = defaultdict(list)
        self.nodes = set()

    def add_edge(self, u, v):
        self.graph[u].append(v)
        self.nodes.add(u)
        self.nodes.add(v)

    def calculate_in_degree(self) -> dict[str,int]:
        in_degree = {node: 0 for node in self.nodes}
        for node in self.graph:
            for neighbor in self.graph[node]:
                in_degree[neighbor] += 1
        return in_degree
    
    def get_nodes_with_no_dependencies(
        self
    ) -> list[str]:
        keys = set(self.graph.keys())
        values = [item for sublist in self.graph.values() for item in sublist]
        items_in_values_not_in_keys = set(values) - keys
        return list(items_in_values_not_in_keys)

    def topological_sort_with_hierarchy(
        self
    ) -> list[list[str]]:
        """Perform a topological sort and return nodes grouped by hierarchy.
        This is a different implementation than the standard because we extract all the
        tasks that have no dependency, create a separate list with them, to add them first
        in the result
        This makes sure we parallelize as possible at all the levels of the build pipeline
        """
        nodes_with_no_dependencies = self.get_nodes_with_no_dependencies()

        # First calculate the degrees as normal
        in_degree = self.calculate_in_degree()

        # Then remove the nodes and their degrees if they don't have any dependency
        self.nodes = [item for item in self.nodes if item not in nodes_with_no_dependencies]
        in_degree = {key: value for key, value in in_degree.items() if key not in nodes_with_no_dependencies}

        queue = deque([node for node in in_degree if in_degree[node] == 0])
        sorted_hierarchy = []

        while queue:
            level_size = len(queue)
            current_level_nodes = []

            for _ in range(level_size):
                node = queue.popleft()
                current_level_nodes.append(node)

                for neighbor in self.graph[node]:
                    if neighbor in in_degree:
                        in_degree[neighbor] -= 1
                        if in_degree[neighbor] == 0:
                            queue.append(neighbor)

            sorted_hierarchy.append(current_level_nodes)

        if sum(len(level) for level in sorted_hierarchy) != len(self.nodes):
            return None  # Graph contains a cycle

        sorted_hierarchy.append(nodes_with_no_dependencies)
        sorted_hierarchy.reverse()
        return sorted_hierarchy