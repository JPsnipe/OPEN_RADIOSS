import tempfile
from pathlib import Path
import sys
import json
import math
from typing import Dict, List

import streamlit as st

root_path = str(Path(__file__).resolve().parents[2])
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from cdb2rad.parser import parse_cdb
from cdb2rad.writer_rad import write_rad


MAX_POINTS = 10000


def viewer_html(nodes: Dict[int, List[float]], max_points: int = MAX_POINTS) -> str:
    """Return a small Three.js viewer for the given nodes.

    If the mesh contains more than ``max_points`` nodes a subset is used in the
    preview to keep the browser responsive.
    """
    if not nodes:
        return "<p>No data</p>"
    coords = list(nodes.values())
    if len(coords) > max_points:
        step = max(1, len(coords) // max_points)
        coords = coords[::step][:max_points]
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
    template = """
<div id='c'></div>
<script src='https://cdn.jsdelivr.net/npm/three@0.154.0/build/three.min.js'></script>
<script>
const pts = {coords};
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(70, 1, 0.1, 1000);
camera.position.z = {cam_dist};
const renderer = new THREE.WebGLRenderer({{antialias:true}});
renderer.setSize(400, 400);
document.getElementById('c').appendChild(renderer.domElement);
const g = new THREE.BufferGeometry();
const verts = new Float32Array(pts.flat());
g.setAttribute('position', new THREE.BufferAttribute(verts, 3));
const m = new THREE.PointsMaterial({{size:2,color:0x0080ff}});
const points = new THREE.Points(g, m);
scene.add(points);
function animate(){{
  requestAnimationFrame(animate);
  points.rotation.y += 0.01;
  renderer.render(scene, camera);
}}
animate();
</script>
"""
    return template.format(coords=json.dumps(coords), cam_dist=cam_dist)


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
        html = viewer_html(nodes)
        if len(nodes) > MAX_POINTS:
            st.caption(
                f"Mostrando un subconjunto de {MAX_POINTS} de {len(nodes)} nodos "
                "para agilizar la vista"
            )
        st.components.v1.html(html, height=420)
else:
    st.info("Sube o selecciona un archivo .cdb")
