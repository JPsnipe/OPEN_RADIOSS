import tempfile
from pathlib import Path
import sys
import json
import math
from typing import Dict, List, Tuple

import streamlit as st

SDEA_LOGO_URL = (
    "https://sdeasolutions.com/wp-content/uploads/2021/11/"
    "cropped-SDEA_Logo-ORIGINAL-250x250-1.jpg"
)
OPENRADIOSS_LOGO_URL = (
    "https://openradioss.org/wp-content/uploads/2023/07/openradioss-logo.png"
)
ANSYS_LOGO_URL = "https://www.ansys.com/content/dam/company/brand/logos/ansys-logos/ansys-logo.svg"

root_path = str(Path(__file__).resolve().parents[2])
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from cdb2rad.parser import parse_cdb
from cdb2rad.writer_rad import write_rad


MAX_EDGES = 10000


def viewer_html(

    nodes: Dict[int, List[float]],
    elements: List[Tuple[int, int, List[int]]],
    max_edges: int = MAX_EDGES,
) -> str:
    """Return an HTML snippet with a lightweight Three.js mesh viewer.


    A subset of ``max_edges`` edges is used when the mesh is large to keep the
    browser responsive.
    """

    if not nodes or not elements:
        return "<p>No data</p>"

    coords = list(nodes.values())
    if len(coords) > max_edges:
        step = max(1, len(coords) // max_edges)
        coords = coords[::step][:max_edges]

    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    zs = [c[2] for c in coords]
    cx = sum(xs) / len(xs)
    cy = sum(ys) / len(ys)
    cz = sum(zs) / len(zs)
    max_r = 0.0
    for x, y, z in coords:
        r = math.sqrt((x - cx) ** 2 + (y - cy) ** 2 + (z - cz) ** 2)
        if r > max_r:
            max_r = r
    cam_dist = max_r * 3 if max_r > 0 else 10.0

    def elem_edges(nids: List[int]) -> List[Tuple[int, int]]:
        if len(nids) == 4:  # shell quad
            idx = [(0, 1), (1, 2), (2, 3), (3, 0)]
        elif len(nids) == 3:  # shell tri
            idx = [(0, 1), (1, 2), (2, 0)]
        elif len(nids) in (8, 20):  # brick/hex
            idx = [
                (0, 1), (1, 2), (2, 3), (3, 0),
                (4, 5), (5, 6), (6, 7), (7, 4),
                (0, 4), (1, 5), (2, 6), (3, 7),
            ]
        elif len(nids) in (4, 10):  # tetra
            idx = [
                (0, 1), (1, 2), (2, 0),
                (0, 3), (1, 3), (2, 3),
            ]
        else:
            idx = [(i, (i + 1) % len(nids)) for i in range(len(nids))]
        return [(nids[a], nids[b]) for a, b in idx if a < len(nids) and b < len(nids)]

    edges = []
    seen = set()
    for _eid, _et, nids in elements:
        for a, b in elem_edges(nids):
            key = tuple(sorted((a, b)))
            if key in seen:
                continue
            if a in nodes and b in nodes:
                seen.add(key)
                edges.append(nodes[a] + nodes[b])
            if len(edges) >= max_edges:
                break
        if len(edges) >= max_edges:
            break

    template = """
<div id='c'></div>
<script src='https://cdn.jsdelivr.net/npm/three@0.154.0/build/three.min.js'></script>
<script src='https://cdn.jsdelivr.net/npm/three@0.154.0/examples/js/controls/OrbitControls.js'></script>
<script>
const segments = {segs};
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(70, 1, 0.1, 1000);
camera.position.set({cam_dist}, {cam_dist}, {cam_dist});
const renderer = new THREE.WebGLRenderer({{antialias:true}});
renderer.setSize(400, 400);
document.getElementById('c').appendChild(renderer.domElement);
const g = new THREE.BufferGeometry();
const verts = new Float32Array(segments.flat());
g.setAttribute('position', new THREE.BufferAttribute(verts, 3));
const m = new THREE.LineBasicMaterial({{color:0x0080ff}});
const lines = new THREE.LineSegments(g, m);
scene.add(lines);
const controls = new THREE.OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
function animate(){{
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
}}
animate();
</script>
"""
    return template.format(segs=json.dumps(edges), cam_dist=cam_dist)


@st.cache_data(ttl=3600)
def load_cdb(path: str):
    return parse_cdb(path)


SDEA_BLUE = "#1989FB"
SDEA_ORANGE = "#FFBC7D"
SDEA_DARK = "#1B1825"

style = f"""
<style>
.stApp {{
    background-color: #000000;
    color: white;
}}
.sdea-header {{
    background-color: {SDEA_DARK};
    padding: 10px;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}}
.sdea-header img {{
    height: 60px;
}}
div.stButton>button {{
    background-color: {SDEA_BLUE};
    color: white;
}}
</style>
"""
st.markdown(style, unsafe_allow_html=True)

st.title("CDB → OpenRadioss")

header = st.container()
with header:
    st.markdown('<div class="sdea-header">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.image(SDEA_LOGO_URL, width=120)
    with col2:
        st.image(OPENRADIOSS_LOGO_URL, width=140)
    with col3:
        st.image(ANSYS_LOGO_URL, width=120)
    st.markdown("</div>", unsafe_allow_html=True)

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
        from cdb2rad.utils import element_summary

        etype_counts, kw_counts = element_summary(elements)
        st.write("Tipos de elemento (CDB):")
        for et, cnt in sorted(etype_counts.items()):
            st.write(f"- Tipo {et}: {cnt} elementos")
        st.write("Tipos en Radioss:")
        for kw, cnt in kw_counts.items():
            st.write(f"- {kw}: {cnt}")
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
                st.write("Resumen de elementos traducidos:")
                for kw, cnt in kw_counts.items():
                    st.write(f"- {kw}: {cnt}")
                lines = mesh_path.read_text().splitlines()[:20]
                st.code("\n".join(lines))

    with preview_tab:
        html = viewer_html(nodes, elements)
        if len(elements) > MAX_EDGES:
            st.caption(
                f"Mostrando un subconjunto de {MAX_EDGES} de {len(elements)} "
                "elementos para agilizar la vista"
            )
        st.components.v1.html(html, height=420)
else:
    st.info("Sube un archivo .cdb")
