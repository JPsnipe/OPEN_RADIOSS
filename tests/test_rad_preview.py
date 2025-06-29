from cdb2rad import rad_preview

def test_extract_block_material():
    sample = """/MAT/LAW1/1\nSteel\n# RHO\n7800\n# E Nu\n210000 0.3\n/END\n"""
    out = rad_preview._extract_block(sample, "/MAT/")
    lines = out.splitlines()
    assert lines[0].startswith("/MAT/LAW1/1")
    assert len(lines) > 2


def test_preview_part_no_material():
    part = {"id": 1, "name": "P1", "pid": 1, "mid": 1}
    txt = rad_preview.preview_part(part)
    assert "/PART/1" in txt
    assert "P1" in txt



def test_preview_bc_types():
    bc_fix = {"type": "BCS", "name": "Fix", "tra": "111", "rot": "111"}
    txt_fix = rad_preview.preview_bc(bc_fix)
    assert "/BCS/1" in txt_fix
    assert "Fix" in txt_fix

    bc_motion = {
        "type": "PRESCRIBED_MOTION",
        "name": "Move",
        "dir": 1,
        "value": 5.0,
        "nodes": [1],
    }
    txt_mov = rad_preview.preview_bc(bc_motion)
    assert "/BOUNDARY/PRESCRIBED_MOTION/1" in txt_mov
    assert "Move" in txt_mov


def test_preview_material_with_fail():
    mat = {
        "id": 1,
        "LAW": "LAW1",
        "EX": 210000,
        "NUXY": 0.3,
        "DENS": 7800.0,
        "FAIL": {"TYPE": "JOHNSON", "D1": -0.09},
    }
    txt = rad_preview.preview_material(mat)
    lines = txt.splitlines()
    assert any(l.startswith("/FAIL/JOHNSON/1") for l in lines)
    fail_idx = next(i for i, l in enumerate(lines) if l.startswith("/FAIL/JOHNSON/1"))
    assert fail_idx + 1 < len(lines)


def test_preview_remote_point():
    rp = {"id": 10, "coords": (1.0, 2.0, 3.0)}
    txt = rad_preview.preview_remote_point(rp)
    lines = txt.splitlines()
    assert lines[0] == "/NODE"
    assert "10" in lines[1]
    assert "1.000000" in lines[1]

