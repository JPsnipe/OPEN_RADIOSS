from cdb2rad.remote import add_remote_point, next_free_node_id


def test_next_free_id():
    nodes = {1: [0.0, 0.0, 0.0], 3: [1.0, 0.0, 0.0]}
    nid = next_free_node_id(nodes)
    assert nid not in nodes


def test_add_remote_point_auto():
    nodes = {1: [0.0, 0.0, 0.0]}
    new_nodes, rp = add_remote_point(nodes, (1.0, 2.0, 3.0))
    assert rp["id"] in new_nodes and new_nodes[rp["id"]] == [1.0, 2.0, 3.0]
    assert rp["id"] != 1
    assert rp["label"] == f"REMOTE_{rp['id']}"


def test_add_remote_point_manual():
    nodes = {1: [0.0, 0.0, 0.0]}
    new_nodes, rp = add_remote_point(nodes, (0.0, 1.0, 0.0), node_id=5, label="P1", mass=2.0)
    assert rp["id"] == 5
    assert new_nodes[5] == [0.0, 1.0, 0.0]
    assert rp["label"] == "P1"
    assert rp["mass"] == 2.0

