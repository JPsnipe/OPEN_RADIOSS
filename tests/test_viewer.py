from cdb2rad.parser import parse_cdb
from src.dashboard.app import viewer_html
import os

DATA = os.path.join(os.path.dirname(__file__), '..', 'data', 'model.cdb')


def test_viewer_html_basic():
    nodes, elements, *_ = parse_cdb(DATA)
    html = viewer_html(nodes, elements)
    assert 'plotly' in html
    assert 'Plotly.newPlot' in html


def test_viewer_html_subset():
    nodes, elements, *_ = parse_cdb(DATA)
    subset = {e[0] for e in elements[:2]}
    html = viewer_html(nodes, elements, selected_eids=subset)
    assert 'plotly' in html
