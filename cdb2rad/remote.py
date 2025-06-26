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
    *,
    node_id: int | None = None,
    label: str | None = None,
    mass: float | None = None,
) -> Tuple[Dict[int, List[float]], Dict[str, object]]:
    """Return updated nodes and remote point metadata."""
    if node_id is None:
        node_id = next_free_node_id(nodes)
    elif node_id in nodes:
        raise ValueError("Node ID already exists")
    new_nodes = dict(nodes)
    new_nodes[node_id] = list(coords)
    rp = {
        "id": node_id,
        "coords": coords,
        "label": label or f"REMOTE_{node_id}",
    }
    if mass is not None:
        rp["mass"] = float(mass)
    return new_nodes, rp
