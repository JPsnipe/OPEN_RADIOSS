import cdb2rad.utils as utils

def test_check_rad_inputs_basic():
    res = utils.check_rad_inputs(
        use_cdb_mats=True,
        materials={1: {"LAW": "LAW1"}},
        use_impact=False,
        impact_materials=None,
        bcs=None,
        interfaces=None,
        properties=[{"id": 1, "type": "SHELL", "thickness": 1.0}],
        parts=[{"id": 1, "pid": 1, "mid": 1}],
    )
    assert all(ok for ok, _ in res)
