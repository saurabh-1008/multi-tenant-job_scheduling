from collections import defaultdict, deque


class CycleError(Exception):
    pass


def topological_order(tasks: list[dict]) -> list[str]:
    """
    tasks: [{"name": "a", "depends_on": []}, {"name": "b", "depends_on": ["a"]}, ...]
    Returns task names in an order where every dependency comes before its dependents.
    """
    graph = defaultdict(list)
    in_degree = {t["name"]: 0 for t in tasks}

    for task in tasks:
        for dep in task["depends_on"]:
            graph[dep].append(task["name"])
            in_degree[task["name"]] += 1

    queue = deque([name for name, deg in in_degree.items() if deg == 0])
    order = []

    while queue:
        current = queue.popleft()
        order.append(current)
        for neighbor in graph[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(order) != len(tasks):
        raise CycleError("Workflow definition contains a cycle — cannot schedule.")

    return order


def get_ready_tasks(tasks: list[dict], completed: set[str]) -> list[str]:
    """
    Given which tasks are already done, return tasks whose dependencies
    are all satisfied and that haven't run yet — these can be dispatched now.
    """
    ready = []
    for task in tasks:
        if task["name"] in completed:
            continue
        if all(dep in completed for dep in task["depends_on"]):
            ready.append(task["name"])
    return ready