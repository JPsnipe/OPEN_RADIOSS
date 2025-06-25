import tempfile
from pathlib import Path
import sys
import json
from typing import Dict, List, Tuple

import streamlit as st

root_path = str(Path(__file__).resolve().parents[2])
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from cdb2rad.parser import parse_cdb
from cdb2rad.writer_rad import write_rad


MAX_FACES = 20000


def viewer_html(
    nodes: Dict[int, List[float]],
    elements: List[Tuple[int, int, List[int]]],
    max_faces: int = MAX_FACES,
) -> Tuple[str, bool]:
    """Return an HTML Plotly viewer showing element surfaces."""
    if not nodes or not elements:
        return "<p>No data</p>", False

    node_ids = list(nodes.keys())
    idx = {nid: i for i, nid in enumerate(node_ids)}
    xs = [nodes[nid][0] for nid in node_ids]
    ys = [nodes[nid][1] for nid in node_ids]
    zs = [nodes[nid][2] for nid in node_ids]

    faces = []
    for _eid, etype, conn in elements:
        if etype in {4, 45, 181, 182}:
            if len(conn) >= 3:
                faces.append((idx[conn[0]], idx[conn[1]], idx[conn[2]]))
            if len(conn) >= 4:
                faces.append((idx[conn[0]], idx[conn[2]], idx[conn[3]]))
        elif etype in {1, 185, 186} and len(conn) >= 8:
            n = conn
            faces.extend(
                [
                    (idx[n[0]], idx[n[1]], idx[n[2]]),
                    (idx[n[0]], idx[n[2]], idx[n[3]]),
                    (idx[n[4]], idx[n[5]], idx[n[6]]),
                    (idx[n[4]], idx[n[6]], idx[n[7]]),
                    (idx[n[0]], idx[n[1]], idx[n[5]]),
                    (idx[n[0]], idx[n[5]], idx[n[4]]),
                    (idx[n[1]], idx[n[2]], idx[n[6]]),
                    (idx[n[1]], idx[n[6]], idx[n[5]]),
                    (idx[n[2]], idx[n[3]], idx[n[7]]),
                    (idx[n[2]], idx[n[7]], idx[n[6]]),
                    (idx[n[3]], idx[n[0]], idx[n[4]]),
                    (idx[n[3]], idx[n[4]], idx[n[7]]),
                ]
            )
        elif etype == 187 and len(conn) >= 4:
            n = conn
            faces.extend(
                [
                    (idx[n[0]], idx[n[1]], idx[n[2]]),
                    (idx[n[0]], idx[n[1]], idx[n[3]]),
                    (idx[n[1]], idx[n[2]], idx[n[3]]),
                    (idx[n[2]], idx[n[0]], idx[n[3]]),
                ]
            )

    show_subset = False
    if len(faces) > max_faces:
        step = max(1, len(faces) // max_faces)
        faces = faces[::step][:max_faces]
        show_subset = True

    if not faces:
        return "<p>No faces to display</p>", False

    i, j, k = zip(*faces)
    data = [
        {
            "type": "mesh3d",
            "x": xs,
            "y": ys,
            "z": zs,
            "i": list(i),
            "j": list(j),
            "k": list(k),
            "color": "#b2b2ff",
            "opacity": 0.8,
        }
    ]

    template = """
<div id='meshplot'></div>
<script src='https://cdn.plot.ly/plotly-2.24.1.min.js'></script>
<script>
const data = {data};
Plotly.newPlot('meshplot', data, {margin:{l:0,r:0,b:0,t:0},scene:{aspectmode:'data'}});
</script>
"""
    return template.format(data=json.dumps(data)), show_subset


@st.cache_data(ttl=3600)
def load_cdb(path: str):
    return parse_cdb(path)


st.title("CDB → OpenRadioss")

# Display SDEA logo
logo_path = Path(__file__).parent / "assets" / "sdea_logo.png"
if logo_path.exists():
    st.image(str(logo_path), width=150)

uploaded = st.file_uploader("Subir archivo .cdb", type="cdb")
example_dir = Path("data_files")
examples = [p.name for p in example_dir.glob("*.cdb")]
selected = st.selectbox("o escoger ejemplo", [""] + examples)

file_path = None
if uploaded is not None:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".cdb")
    tmp.write(uploaded.getvalue())
    tmp.close()
    file_path = tmp.name
elif selected:
    file_path = str(example_dir / selected)

if file_path:
    nodes, elements, node_sets, elem_sets, materials = load_cdb(file_path)
    info_tab, preview_tab = st.tabs(["Información", "Vista 3D"])

    with info_tab:
        st.write("Nodos:", len(nodes))
        st.write("Elementos:", len(elements))
        st.write("Conjuntos de nodos:", len(node_sets))
        for name, nids in node_sets.items():
            st.write(f"- {name}: {len(nids)} nodos")
        st.write("Conjuntos de elementos:", len(elem_sets))
        for name, eids in elem_sets.items():
            st.write(f"- {name}: {len(eids)} elementos")
        st.write("Materiales:")
        for mid, props in materials.items():
            st.write(f"- ID {mid}: {props}")

        if st.button("Generar input deck"):
            with tempfile.TemporaryDirectory() as tmpdir:
                rad_path = Path(tmpdir) / "model_0000.rad"
                mesh_path = Path(tmpdir) / "mesh.inp"
                write_rad(
                    nodes,
                    elements,
                    str(rad_path),
                    mesh_inc=str(mesh_path),
                    node_sets=node_sets,
                    elem_sets=elem_sets,
                    materials=materials,
                )
                st.success("Ficheros generados en directorio temporal")
                lines = mesh_path.read_text().splitlines()[:20]
                st.code("\n".join(lines))

    with preview_tab:
        html, subset = viewer_html(nodes, elements)
        if subset:
            st.caption(
                f"Mostrando un subconjunto de {MAX_FACES} caras para agilizar la vista"
            )
        st.components.v1.html(html, height=420)
else:
    st.info("Sube o selecciona un archivo .cdb")
