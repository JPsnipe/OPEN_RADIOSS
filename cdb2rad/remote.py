from typing import Dict, List, Tuple


def next_free_node_id(nodes: Dict[int, List[float]]) -> int:
    """Return the next available node ID not used in *nodes*."""
    nid = max(nodes.keys(), default=0) + 1
    while nid in nodes:
        nid += 1
    return nid


def add_remote_point(
    nodes: Dict[int, List[float]],
    coords: Tuple[float, float, float],
    node_id: int | None = None,
) -> Tuple[Dict[int, List[float]], int]:
    """Return a new node dictionary including a remote point."""
    if node_id is None:
        node_id = next_free_node_id(nodes)
    elif node_id in nodes:
        raise ValueError("Node ID already exists")
    new_nodes = dict(nodes)
    new_nodes[node_id] = list(coords)
    return new_nodes, node_id
