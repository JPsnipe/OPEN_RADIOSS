import os
from cdb2rad.parser import parse_cdb
from cdb2rad.writer_inp import write_inp

DATA = os.path.join(os.path.dirname(__file__), '..', 'data', 'model.cdb')


def test_write_inp(tmp_path):
    nodes, elements, node_sets, elem_sets, _ = parse_cdb(DATA)
    out = tmp_path / 'model.inp'
    write_inp(nodes, elements, str(out), node_sets=node_sets, elem_sets=elem_sets)
    txt = out.read_text()
    assert '*NODE' in txt
    assert '*ELEMENT' in txt
    assert '*NSET' in txt
    assert '*ELSET' in txt
