import os
from cdb2rad.parser import parse_cdb
from cdb2rad.writer_inc import write_mesh_inc
from cdb2rad.writer_rad import write_starter, write_engine
from cdb2rad.utils import element_summary, element_set_etypes
from cdb2rad.material_defaults import apply_default_materials

DATA = os.path.join(os.path.dirname(__file__), '..', 'data', 'model.cdb')


def test_parse_cdb():
    nodes, elements, node_sets, elem_sets, materials = parse_cdb(DATA)
    assert len(nodes) == 2032
    assert len(elements) == 2479
    assert "BALL" in elem_sets
    assert "TARGET" in elem_sets
    assert elem_sets["BALL"][0] == 1
    assert elem_sets["BALL"][-1] == 715
    assert elem_sets["TARGET"][0] == 918
    assert elem_sets["TARGET"][-1] == 2681


def test_element_summary():
    _, elements, _, _, _ = parse_cdb(DATA)
    etype_counts, kw_counts = element_summary(elements)
    assert sum(kw_counts.values()) == len(elements)
    assert kw_counts["BRICK"] > 0


def test_write_mesh(tmp_path):
    nodes, elements, node_sets, elem_sets, materials = parse_cdb(DATA)
    out = tmp_path / 'mesh.inc'
    write_mesh_inc(
        nodes,
        elements,
        str(out),
        node_sets=node_sets,
        elem_sets=elem_sets,
        materials=materials,
    )
    text = out.read_text()
    assert '/NODE' in text
    assert '/BRICK' in text


def test_write_rad(tmp_path):
    nodes, elements, node_sets, elem_sets, materials = parse_cdb(DATA)
    starter = tmp_path / 'model_0000.rad'
    engine = tmp_path / 'model_0001.rad'
    write_starter(
        nodes,
        elements,
        str(starter),
        node_sets=node_sets,
        elem_sets=elem_sets,
        materials=materials,
        thickness=2.0,
        young=1e5,
        poisson=0.25,
        density=7000.0,
        runname="demo",
    )
    write_engine(
        str(engine),
        runname="demo",
        t_end=0.02,
        anim_dt=0.002,
        tfile_dt=0.0001,
        dt_ratio=0.8,
    )
    content = starter.read_text()
    assert content.startswith('#RADIOSS STARTER')
    assert '/BEGIN' in content
    assert '/END' in content
    assert '200000.0' in content
    assert '2022         0' not in content
    assert '2022' in content
    assert '1                  2                  3' in content

    eng_txt = engine.read_text()
    assert '/RUN/demo/1' in eng_txt
    assert '0.02' in eng_txt
    assert '0.002' in eng_txt
    assert '0.0001' in eng_txt


def test_write_rad_extra_materials(tmp_path):
    nodes, elements, node_sets, elem_sets, materials = parse_cdb(DATA)
    extra = {
        99: {
            'LAW': 'LAW2',
            'EX': 1e5,
            'NUXY': 0.3,
            'DENS': 7800.0,
            'A': 200.0,
            'B': 400.0,
            'N': 0.5,
            'C': 0.01,
            'EPS0': 1.0,
        }
    }
    starter = tmp_path / 'model_extra_0000.rad'
    write_starter(
        nodes,
        elements,
        str(starter),
        node_sets=node_sets,
        elem_sets=elem_sets,
        materials=materials,
        extra_materials=extra,
    )
    txt = starter.read_text()
    assert '/MAT/LAW2/99' in txt

def test_write_mesh_without_sets_materials(tmp_path):
    nodes, elements, node_sets, elem_sets, materials = parse_cdb(DATA)
    out = tmp_path / 'mesh_no_sets.inc'
    write_mesh_inc(nodes, elements, str(out))
    content = out.read_text()
    assert '/GRNOD' not in content
    assert '/SET/EL' not in content
    assert '/MAT/LAW1' not in content



def test_write_rad_with_bc(tmp_path):
    nodes, elements, *_ = parse_cdb(DATA)
    rad = tmp_path / 'bc_0000.rad'
    bc = [{
        'name': 'fixed',
        'tra': '111',
        'rot': '111',
        'nodes': [1, 2]
    }]
    write_starter(nodes, elements, str(rad), boundary_conditions=bc)
    txt = rad.read_text()
    assert '/BCS/1' in txt
    assert 'fixed' in txt


def test_write_rad_with_bc_set(tmp_path):
    nodes, elements, node_sets, *_ = parse_cdb(DATA)
    rad = tmp_path / 'bc_set_0000.rad'
    bc = [{
        'name': 'fixed',
        'tra': '111',
        'rot': '111',
        'set': 'SUFACE_BALL'
    }]
    write_starter(nodes, elements, str(rad), node_sets=node_sets, boundary_conditions=bc)
    txt = rad.read_text()
    assert '/BCS/1' in txt
    assert '/GRNOD/NODE/1' not in txt


def test_write_rad_with_prescribed(tmp_path):
    nodes, elements, *_ = parse_cdb(DATA)
    rad = tmp_path / 'prescribed_0000.rad'
    bc = [{
        'name': 'move',
        'type': 'PRESCRIBED_MOTION',
        'dir': 1,
        'value': 5.0,
        'nodes': [1, 2]
    }]
    write_starter(nodes, elements, str(rad), boundary_conditions=bc)
    txt = rad.read_text()
    assert '/BOUNDARY/PRESCRIBED_MOTION/1' in txt


def test_write_rad_with_impvel(tmp_path):
    nodes, elements, *_ = parse_cdb(DATA)
    rad = tmp_path / 'vel_0000.rad'
    write_starter(nodes, elements, str(rad), init_velocity={'nodes': [1], 'vx': 10.0})
    txt = rad.read_text()
    assert '/IMPVEL/1' in txt


def test_write_rad_with_gravity(tmp_path):
    nodes, elements, *_ = parse_cdb(DATA)
    rad = tmp_path / 'grav_0000.rad'
    write_starter(nodes, elements, str(rad), gravity={'g': 9.81, 'nz': -1.0})
    txt = rad.read_text()
    assert '/GRAV' in txt


def test_write_rad_with_type7_contact(tmp_path):
    nodes, elements, *_ = parse_cdb(DATA)
    rad = tmp_path / 'contact7_0000.rad'
    inter = [{
        'type': 'TYPE7',
        'name': 'cnt7',
        'slave': [1, 2],
        'master': [3, 4],
        'fric': 0.2,
    }]
    write_starter(nodes, elements, str(rad), interfaces=inter)
    txt = rad.read_text()
    assert '/INTER/TYPE7/1' in txt
    assert '/FRICTION' in txt
    for line in txt.splitlines():
        if line.startswith('/INTER/TYPE7'):
            assert not line.startswith(' ')


def test_write_rad_with_type2_contact(tmp_path):
    nodes, elements, *_ = parse_cdb(DATA)
    rad = tmp_path / 'contact2_0000.rad'
    inter = [{
        'type': 'TYPE2',
        'name': 'cnt2',
        'slave': [1, 2],
        'master': [3, 4],
        'fric': 0.1,
    }]
    write_starter(nodes, elements, str(rad), interfaces=inter)
    txt = rad.read_text()
    assert '/INTER/TYPE2/1' in txt
    assert '/FRICTION' in txt
    for line in txt.splitlines():
        if line.startswith('/INTER/TYPE2'):
            assert not line.startswith(' ')



def test_write_rad_advanced_options(tmp_path):
    nodes, elements, node_sets, elem_sets, mats = parse_cdb(DATA)
    starter = tmp_path / 'advanced_0000.rad'
    engine = tmp_path / 'advanced_0001.rad'
    write_starter(
        nodes,
        elements,
        str(starter),
        node_sets=node_sets,
        elem_sets=elem_sets,
        materials=mats,
    )
    write_engine(
        str(engine),
        print_n=-250,
        print_line=55,
        rfile_cycle=10,
        rfile_n=2,
        h3d_dt=0.005,
        stop_emax=1.0,
        stop_mmax=0.0,
        stop_nmax=0.0,
        stop_nth=1,
        stop_nanim=1,
        stop_nerr=0,
        adyrel=(0.0, 0.02),
    )
    text = engine.read_text()
    assert '/RFILE/2' in text
    assert '/H3D/DT' in text
    assert '/ADYREL' in text


def test_write_rad_extra_outputs(tmp_path):
    nodes, elements, *_ = parse_cdb(DATA)
    starter = tmp_path / 'extra_outputs_0000.rad'
    engine = tmp_path / 'extra_outputs_0001.rad'
    write_starter(nodes, elements, str(starter))
    write_engine(
        str(engine),
        shell_anim_dt=0.003,
        brick_anim_dt=0.002,
        hisnoda_dt=0.004,
        rfile_dt=0.005,
        out_ascii=True,
        t_init=0.1,
    )
    txt = engine.read_text()
    assert '/ANIM/SHELL/DT' in txt
    assert '/ANIM/BRICK/DT' in txt
    assert '/HISNODA/DT' in txt
    assert '/RFILE/DT' in txt
    assert '/OUTP/ASCII' in txt
    assert '0.1' in txt


def test_write_rad_adyrel_none(tmp_path):
    nodes, elements, *_ = parse_cdb(DATA)
    starter = tmp_path / 'adyrel_none_0000.rad'
    engine = tmp_path / 'adyrel_none_0001.rad'
    write_starter(nodes, elements, str(starter))
    write_engine(str(engine), adyrel=(None, None))
    txt = engine.read_text()
    assert '/ADYREL' not in txt


def test_write_rad_without_include(tmp_path):
    nodes, elements, *_ = parse_cdb(DATA)
    rad = tmp_path / 'noinc_0000.rad'
    write_starter(nodes, elements, str(rad), include_inc=False)
    content = rad.read_text()
    assert '#include' not in content


def test_write_rad_skip_controls(tmp_path):
    nodes, elements, *_ = parse_cdb(DATA)
    starter = tmp_path / 'skip_0000.rad'
    engine = tmp_path / 'skip_0001.rad'
    write_starter(nodes, elements, str(starter))
    write_engine(
        str(engine),
        anim_dt=None,
        tfile_dt=None,
        dt_ratio=None,
        print_n=None,
        print_line=None,
    )
    txt = engine.read_text()
    assert '/ANIM/DT' not in txt
    assert '/TFILE' not in txt
    assert '/DT/NODA' not in txt
    assert '/PRINT' not in txt


def test_write_rad_with_connectors(tmp_path):
    nodes, elements, *_ = parse_cdb(DATA)
    rad = tmp_path / 'conn_0000.rad'
    rb = [{
        'RBID': 1,
        'Gnod_id': list(nodes.keys())[0],
        'nodes': [list(nodes.keys())[1]],
    }]
    rbe2 = [{
        'name': 'c2',
        'N_master': list(nodes.keys())[0],
        'N_slave_list': [list(nodes.keys())[1]],
    }]
    rbe3 = [{
        'name': 'c3',
        'N_dependent': list(nodes.keys())[0],
        'independent': [(list(nodes.keys())[1], 1.0)],
    }]
    write_starter(nodes, elements, str(rad), rbody=rb, rbe2=rbe2, rbe3=rbe3)
    text = rad.read_text()
    assert '/RBODY/1' in text
    assert '/RBE2/1' in text
    assert '/RBE3/1' in text


def test_write_rad_with_properties(tmp_path):
    nodes, elements, *_ = parse_cdb(DATA)
    rad = tmp_path / 'prop_0000.rad'
    props = [
        {'id': 1, 'name': 'shell_prop', 'type': 'SHELL', 'thickness': 1.2}
    ]
    parts = [
        {'id': 1, 'name': 'part1', 'pid': 1, 'mid': 1}
    ]
    write_starter(nodes, elements, str(rad), properties=props, parts=parts)
    txt = rad.read_text()
    assert '/PROP/SHELL/1' in txt
    assert '/PART/1' in txt



def test_write_rad_with_advanced_shell(tmp_path):
    nodes, elements, *_ = parse_cdb(DATA)
    rad = tmp_path / 'prop_adv_0000.rad'
    props = [
        {
            'id': 1,
            'name': 'adv',
            'type': 'SHELL',
            'thickness': 1.2,
            'Ishell': 22,
            'Iplas': 0,
            'Ithick': 0,
            'Istrain': 1,
            'Ashear': 1,
            'hm': 0.1,
            'hf': 0.2,
            'hr': 0.3,
            'dm': 0.4,
            'dn': 0.5,
        }
    ]
    write_starter(nodes, elements, str(rad), properties=props)
    lines = rad.read_text().splitlines()
    idx = lines.index('/PROP/SHELL/1')
    nums1 = lines[idx + 3].split()
    nums2 = lines[idx + 5].split()
    nums3 = lines[idx + 7].split()
    assert nums1[0] == '22'
    assert nums2[0] == '0.1'
    assert nums3[1] == '1'
    assert nums3[2] == '1.2'


def test_write_rad_with_solid_prop(tmp_path):
    nodes, elements, *_ = parse_cdb(DATA)
    rad = tmp_path / 'solid_0000.rad'
    props = [
        {
            'id': 1,
            'name': 'solid_p',
            'type': 'SOLID',

            'Isolid': 22,
            'Ismstr': 5,
            'Icpre': 2,
            'Iframe': 3,
            'Inpts': 111,
            'qa': 1.5,
            'qb': 0.1,
            'dn': 0.2,
            'h': 0.3,
            'dtmin': 0.04,
            'Ndir': 2,
            'sphpart_ID': 9,

        }
    ]
    parts = [{
        'id': 1,
        'name': 'part1',
        'pid': 1,
        'mid': 1,
    }]
    write_starter(nodes, elements, str(rad), properties=props, parts=parts)
    lines = rad.read_text().splitlines()
    idx = lines.index('/PROP/SOLID/1')
    assert 'Isolid' in lines[idx + 2]
    nums = lines[idx + 3].split()

    nums2 = lines[idx + 5].split()
    assert nums[0] == '22'
    assert nums2[0] == '111'
    nums3 = lines[idx + 7].split()
    assert nums3[0] == "0.04"
    assert nums3[1] == "2"
    assert nums3[2] == "9"
    assert nums2[1] == "1.5"


def test_write_starter_si_units(tmp_path):
    nodes, elements, node_sets, elem_sets, materials = parse_cdb(DATA)
    rad = tmp_path / 'si_units_0000.rad'
    write_starter(
        nodes,
        elements,
        str(rad),
        node_sets=node_sets,
        elem_sets=elem_sets,
        materials=materials,
        unit_sys="SI",
    )
    txt = rad.read_text()
    assert '2017         0' in txt
    assert 'kg                  mm                  ms' in txt


def test_element_set_etypes():
    nodes, elements, node_sets, elem_sets, _ = parse_cdb(DATA)
    info = element_set_etypes(elements, elem_sets)
    # Expect at least one recognized Ansys type in the BALL set
    assert any(v > 0 for v in info.get('BALL', {}).values())




