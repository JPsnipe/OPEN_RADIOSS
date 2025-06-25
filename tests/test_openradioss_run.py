import os
import subprocess
from pathlib import Path
import pytest
from cdb2rad.parser import parse_cdb
from cdb2rad.writer_rad import write_rad

DATA = Path(__file__).resolve().parents[1] / 'data' / 'model.cdb'
EXEC = Path(__file__).resolve().parents[1] / 'openradioss_bin' / 'OpenRadioss' / 'exec' / 'starter_linux64_gf'
LIBDIR = Path(__file__).resolve().parents[1] / 'openradioss_bin' / 'OpenRadioss' / 'extlib' / 'hm_reader' / 'linux64'
CFGDIR = Path(__file__).resolve().parents[1] / 'openradioss_bin' / 'OpenRadioss' / 'hm_cfg_files'

@pytest.mark.skipif(not EXEC.exists(), reason="OpenRadioss binary not installed")
def test_run_starter(tmp_path):
    nodes, elements, node_sets, elem_sets, mats = parse_cdb(str(DATA))
    rad = tmp_path / 'model_0000.rad'
    write_rad(
        nodes,
        elements,
        str(rad),
        node_sets=node_sets,
        elem_sets=elem_sets,
        materials=mats,
        thickness=1.0,
        young=210000.0,
        poisson=0.3,
        density=7800.0,
    )
    env = os.environ.copy()
    env['LD_LIBRARY_PATH'] = str(LIBDIR)
    env['RAD_CFG_PATH'] = str(CFGDIR)
    result = subprocess.run([str(EXEC), '-i', str(rad)], env=env, capture_output=True, text=True)
    assert 'OpenRadioss Starter' in result.stdout
