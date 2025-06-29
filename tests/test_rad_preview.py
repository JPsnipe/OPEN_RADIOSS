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
