from cdb2rad.parser import parse_cdb
from src.dashboard.app import viewer_html
import os

DATA = os.path.join(os.path.dirname(__file__), '..', 'data', 'model.cdb')


def test_viewer_html_basic():
    nodes, elements, *_ = parse_cdb(DATA)
    html = viewer_html(nodes, elements)
    assert 'OrbitControls' in html
    assert 'LineSegments' in html
    assert 'MeshPhongMaterial' in html
    assert 'controls.target' in html
