from cdb2rad.remote import add_remote_point, next_free_node_id


def test_next_free_id():
    nodes = {1: [0.0, 0.0, 0.0], 3: [1.0, 0.0, 0.0]}
    nid = next_free_node_id(nodes)
    assert nid not in nodes


def test_add_remote_point_auto():
    nodes = {1: [0.0, 0.0, 0.0]}
    new_nodes, nid = add_remote_point(nodes, (1.0, 2.0, 3.0))
    assert nid in new_nodes and new_nodes[nid] == [1.0, 2.0, 3.0]
    assert 1 in new_nodes
    assert nid != 1


def test_add_remote_point_manual():
    nodes = {1: [0.0, 0.0, 0.0]}
    new_nodes, nid = add_remote_point(nodes, (0.0, 1.0, 0.0), node_id=5)
    assert nid == 5
    assert new_nodes[5] == [0.0, 1.0, 0.0]

