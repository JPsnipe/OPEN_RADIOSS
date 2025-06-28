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


def test_check_rad_inputs_solid_conflict():
    res = utils.check_rad_inputs(
        use_cdb_mats=True,
        materials={1: {"LAW": "LAW1"}},
        use_impact=False,
        impact_materials=None,
        bcs=None,
        interfaces=None,
        properties=[
            {
                "id": 1,
                "type": "SOLID",
                "Isolid": 24,
                "h": 0.1,
            }
        ],
        parts=[{"id": 1, "pid": 1, "mid": 1}],
        advanced=True,
    )
    assert all(ok for ok, _ in res)
    assert any('WARNING' in msg for _, msg in res)


def test_check_rad_inputs_solid_ok():
    res = utils.check_rad_inputs(
        use_cdb_mats=True,
        materials={1: {"LAW": "LAW1"}},
        use_impact=False,
        impact_materials=None,
        bcs=None,
        interfaces=None,
        properties=[
            {
                "id": 1,
                "type": "SOLID",
                "Isolid": 24,
                "Iframe": 2,
                "dn": 0.1,
            }
        ],
        parts=[{"id": 1, "pid": 1, "mid": 1}],
        advanced=True,
    )
    assert all(ok for ok, _ in res)


def test_check_rad_inputs_shell_conflict():
    res = utils.check_rad_inputs(
        use_cdb_mats=True,
        materials={1: {"LAW": "LAW1"}},
        use_impact=False,
        impact_materials=None,
        bcs=None,
        interfaces=None,
        properties=[
            {
                "id": 1,
                "type": "SHELL",
                "Ishell": 1,
                "thickness": 1.0,
                "hm": 0.2,
            }
        ],
        parts=[{"id": 1, "pid": 1, "mid": 1}],
        advanced=True,
    )
    assert all(ok for ok, _ in res)
    

def test_check_rad_inputs_shell_ok():
    res = utils.check_rad_inputs(
        use_cdb_mats=True,
        materials={1: {"LAW": "LAW1"}},
        use_impact=False,
        impact_materials=None,
        bcs=None,
        interfaces=None,
        properties=[
            {
                "id": 1,
                "type": "SHELL",
                "Ishell": 24,
                "thickness": 1.0,
                "hm": 0.2,
            }
        ],
        parts=[{"id": 1, "pid": 1, "mid": 1}],
        advanced=True,
    )
    assert all(ok for ok, _ in res)
