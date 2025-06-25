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
from cdb2rad.writer_inc import write_mesh_inc


MAX_EDGES = 10000
MAX_FACES = 15000


def viewer_html(

    nodes: Dict[int, List[float]],
    elements: List[Tuple[int, int, List[int]]],
    max_edges: int = MAX_EDGES,
    max_faces: int = MAX_FACES,
) -> str:
    """Return an HTML snippet with a lightweight Three.js mesh viewer.


    A subset of ``max_edges`` edges and ``max_faces`` triangular faces is used
    when the mesh is large to keep the browser responsive.
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
    cam_x = cx + cam_dist
    cam_y = cy + cam_dist
    cam_z = cz + cam_dist

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
    faces = []
    seen = set()

    def add_face(tri: Tuple[int, int, int]):
        if all(n in nodes for n in tri):
            faces.append(nodes[tri[0]] + nodes[tri[1]] + nodes[tri[2]])

    def elem_faces(nids: List[int]) -> List[Tuple[int, int, int]]:
        if len(nids) == 4:  # shell quad
            idx = [(0, 1, 2), (0, 2, 3)]
        elif len(nids) == 3:  # shell tri
            idx = [(0, 1, 2)]
        elif len(nids) in (8, 20):  # brick/hex
            idx = [
                (0, 1, 2), (0, 2, 3),
                (4, 5, 6), (4, 6, 7),
                (0, 1, 5), (0, 5, 4),
                (1, 2, 6), (1, 6, 5),
                (2, 3, 7), (2, 7, 6),
                (3, 0, 4), (3, 4, 7),
            ]
        elif len(nids) in (4, 10):  # tetra
            idx = [
                (0, 1, 2),
                (0, 1, 3),
                (1, 2, 3),
                (0, 2, 3),
            ]
        else:
            idx = []
        return [(nids[a], nids[b], nids[c]) for a, b, c in idx]

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
        for tri in elem_faces(nids):
            add_face(tri)
            if len(faces) >= max_faces:
                break
        if len(edges) >= max_edges and len(faces) >= max_faces:
            break

    template = """
<div id='c'></div>
<script src='https://cdn.jsdelivr.net/npm/three@0.154.0/build/three.min.js'></script>
<script src='https://cdn.jsdelivr.net/npm/three@0.154.0/examples/js/controls/OrbitControls.js'></script>
<script>
const segments = {segs};
const triangles = {tris};
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(70, 1, 0.1, 1000);
camera.position.set({cam_x}, {cam_y}, {cam_z});
const renderer = new THREE.WebGLRenderer({{antialias:true}});
renderer.setSize(400, 400);
document.getElementById('c').appendChild(renderer.domElement);
const g = new THREE.BufferGeometry();
const verts = new Float32Array(segments.flat());
g.setAttribute('position', new THREE.BufferAttribute(verts, 3));
const m = new THREE.LineBasicMaterial({{color:0x0080ff}});
const lines = new THREE.LineSegments(g, m);
scene.add(lines);
const fg = new THREE.BufferGeometry();
const fverts = new Float32Array(triangles.flat());
fg.setAttribute('position', new THREE.BufferAttribute(fverts, 3));
fg.computeVertexNormals();
const fmat = new THREE.MeshPhongMaterial({{color:0xcccccc, side:THREE.DoubleSide, opacity:0.5, transparent:true}});
const mesh = new THREE.Mesh(fg, fmat);
scene.add(mesh);
scene.add(new THREE.AmbientLight(0x404040));
const dlight = new THREE.DirectionalLight(0xffffff, 0.8);
dlight.position.set(1,1,1);
scene.add(dlight);
const controls = new THREE.OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.target.set({cx}, {cy}, {cz});
camera.lookAt({cx}, {cy}, {cz});
function animate(){{
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
}}
animate();
</script>
"""
    return template.format(
        segs=json.dumps(edges),
        tris=json.dumps(faces),
        cam_dist=cam_dist,
        cam_x=cam_x,
        cam_y=cam_y,
        cam_z=cam_z,
        cx=cx,
        cy=cy,
        cz=cz,
    )


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
    info_tab, preview_tab, inp_tab, rad_tab = st.tabs([
        "Información",
        "Vista 3D",
        "Generar INC",
        "Generar RAD",
    ])

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

    with preview_tab:
        html = viewer_html(nodes, elements)
        if len(elements) > MAX_EDGES:
            st.caption(
                f"Mostrando un subconjunto de {MAX_EDGES} de {len(elements)} "
                "elementos para agilizar la vista"
            )
        st.components.v1.html(html, height=420)

    with inp_tab:
        st.subheader("Generar mesh.inc")

        use_sets = st.checkbox("Incluir name selections", value=True)
        use_mats = st.checkbox("Incluir materiales", value=True)

        if st.button("Generar .inc"):
            with tempfile.TemporaryDirectory() as tmpdir:
                inp_path = Path(tmpdir) / "mesh.inc"
                write_mesh_inc(
                    nodes,
                    elements,
                    str(inp_path),
                    node_sets=node_sets if use_sets else None,
                    elem_sets=elem_sets if use_sets else None,
                    materials=materials if use_mats else None,

                )
                st.success("Fichero generado en directorio temporal")
                lines = inp_path.read_text().splitlines()[:20]
                st.code("\n".join(lines))

    with rad_tab:
        st.subheader("Opciones de cálculo")
        thickness = st.number_input("Grosor", value=1.0, min_value=0.0)
        young = st.number_input("Módulo E", value=210000.0)
        poisson = st.number_input("Coeficiente de Poisson", value=0.3)
        density = st.number_input("Densidad", value=7800.0)

        if "impact_materials" not in st.session_state:
            st.session_state["impact_materials"] = []

        with st.expander("Materiales de impacto (Johnson-Cook)"):
            mat_id = st.number_input(
                "ID material", value=len(st.session_state["impact_materials"]) + 1, step=1
            )
            dens_i = st.number_input("Densidad", value=7800.0, key="dens_i")
            e_i = st.number_input("E", value=210000.0, key="e_i")
            nu_i = st.number_input("Poisson", value=0.3, key="nu_i")
            a_i = st.number_input("A", value=200.0, key="a_i")
            b_i = st.number_input("B", value=400.0, key="b_i")
            n_i = st.number_input("n", value=0.5, key="n_i")
            c_i = st.number_input("C", value=0.01, key="c_i")
            eps_i = st.number_input("EPS0", value=1.0, key="eps0_i")
            if st.button("Añadir material"):
                st.session_state["impact_materials"].append(
                    {
                        "id": int(mat_id),
                        "LAW": "LAW2",
                        "EX": e_i,
                        "NUXY": nu_i,
                        "DENS": dens_i,
                        "A": a_i,
                        "B": b_i,
                        "N": n_i,
                        "C": c_i,
                        "EPS0": eps_i,
                    }
                )
            if st.session_state["impact_materials"]:
                st.write("Materiales definidos:")
                for mat in st.session_state["impact_materials"]:
                    st.json(mat)


        st.markdown("### Control del cálculo")
        runname = st.text_input("Nombre de la simulación", value="model")
        t_end = st.number_input("Tiempo final", value=0.01, format="%.5f")
        anim_dt = st.number_input("Paso animación", value=0.001, format="%.5f")
        tfile_dt = st.number_input("Intervalo historial", value=0.00001, format="%.5f")
        dt_ratio = st.number_input(
            "Factor seguridad DT", value=0.9, min_value=0.0, max_value=1.0
        )

        if "bcs" not in st.session_state:
            st.session_state["bcs"] = []
        if "interfaces" not in st.session_state:
            st.session_state["interfaces"] = []
        if "init_vel" not in st.session_state:
            st.session_state["init_vel"] = None

        with st.expander("Condiciones de contorno (BCS)"):
            bc_name = st.text_input("Nombre BC", value="Fixed")
            bc_tra = st.text_input("Traslación (111/000)", value="111")
            bc_rot = st.text_input("Rotación (111/000)", value="111")
            bc_nodes = st.text_input("Nodos comma-sep", value="1,2")
            if st.button("Añadir BC"):
                node_list = [int(n) for n in bc_nodes.split(',') if n.strip()]
                st.session_state["bcs"].append({
                    "name": bc_name,
                    "tra": bc_tra,
                    "rot": bc_rot,
                    "nodes": node_list,
                })
            for bc in st.session_state["bcs"]:
                st.json(bc)

        with st.expander("Interacciones (INTER)"):
            int_name = st.text_input("Nombre interfaz", value="Tie")
            slave_nodes = st.text_input("Nodos esclavos", value="3,4")
            master_nodes = st.text_input("Nodos maestros", value="5,6")
            fric = st.number_input("Fricción", value=0.0)
            if st.button("Añadir interfaz"):
                s_list = [int(n) for n in slave_nodes.split(',') if n.strip()]
                m_list = [int(n) for n in master_nodes.split(',') if n.strip()]
                st.session_state["interfaces"].append({
                    "name": int_name,
                    "slave": s_list,
                    "master": m_list,
                    "fric": fric,
                })
            for itf in st.session_state["interfaces"]:
                st.json(itf)

        with st.expander("Velocidad inicial (IMPVEL)"):
            vel_nodes = st.text_input("Nodos velocidad", value="1")
            vx = st.number_input("Vx", value=0.0)
            vy = st.number_input("Vy", value=0.0)
            vz = st.number_input("Vz", value=0.0)
            if st.button("Asignar velocidad"):
                n_list = [int(n) for n in vel_nodes.split(',') if n.strip()]
                st.session_state["init_vel"] = {"nodes": n_list, "vx": vx, "vy": vy, "vz": vz}
            if st.session_state["init_vel"]:
                st.json(st.session_state["init_vel"])

        use_cdb_mats = st.checkbox("Incluir materiales del CDB", value=True)
        use_impact = st.checkbox(
            "Incluir materiales de impacto", value=True
        )


        if st.button("Generar .rad"):
            with tempfile.TemporaryDirectory() as tmpdir:
                rad_path = Path(tmpdir) / "model_0000.rad"
                mesh_path = Path(tmpdir) / "mesh.inc"
                extra = None
                if use_impact and st.session_state["impact_materials"]:
                    extra = {
                        m["id"]: {
                            k: v
                            for k, v in m.items()
                            if k != "id"
                        }
                        for m in st.session_state["impact_materials"]
                    }
                write_rad(
                    nodes,
                    elements,
                    str(rad_path),
                    mesh_inc=str(mesh_path),
                    node_sets=node_sets,
                    elem_sets=elem_sets,
                    materials=materials if use_cdb_mats else None,
                    extra_materials=extra,
                    thickness=thickness,
                    young=young,
                    poisson=poisson,
                    density=density,

                    runname=runname,
                    t_end=t_end,
                    anim_dt=anim_dt,
                    tfile_dt=tfile_dt,
                    dt_ratio=dt_ratio,

                    boundary_conditions=st.session_state.get("bcs"),
                    interfaces=st.session_state.get("interfaces"),
                    init_velocity=st.session_state.get("init_vel"),

                )
                st.success(
                    f"Ficheros generados en directorio temporal: {rad_path}"
                )
                lines = rad_path.read_text().splitlines()[:20]
                st.code("\n".join(lines))

        if st.button("Generar .zip limpio"):
            with tempfile.TemporaryDirectory() as tmpdir:
                mesh_path = Path(tmpdir) / "mesh.inc"
                rad_path = Path(tmpdir) / "minimal.rad"
                write_mesh_inc(nodes, elements, str(mesh_path))
                from cdb2rad.writer_rad import write_minimal_rad

                write_minimal_rad(str(rad_path), mesh_inc=mesh_path.name)

                zip_path = Path(tmpdir) / "clean.zip"
                import zipfile

                with zipfile.ZipFile(zip_path, "w") as zf:
                    zf.write(rad_path, arcname=rad_path.name)
                    zf.write(mesh_path, arcname=mesh_path.name)
                st.success("Archivo clean.zip generado")
                st.write(zip_path)
else:
    st.info("Sube un archivo .cdb")
