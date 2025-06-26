import tempfile
from pathlib import Path
import sys
import json
import math
import subprocess
from typing import Dict, List, Tuple, Optional, Set

# Ensure repository root is on the Python path before importing local modules
root_path = str(Path(__file__).resolve().parents[2])
if root_path not in sys.path:
    sys.path.insert(0, root_path)

import streamlit as st
from cdb2rad.mesh_convert import convert_to_vtk, mesh_to_temp_vtk

from cdb2rad.vtk_writer import write_vtk, write_vtp


def _rerun():
    """Compatibility wrapper for streamlit rerun."""
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()



def launch_paraview_server(
    mesh_path: str | None = None,
    *,
    nodes: Dict[int, List[float]] | None = None,
    elements: List[Tuple[int, int, List[int]]] | None = None,
    port: int = 12345,
    host: str = "127.0.0.1",
    verbose: bool = False,
) -> str:

    """Spawn ParaViewWeb server for ``mesh_path`` or an in-memory mesh."""
    script = Path(__file__).resolve().parents[2] / "scripts" / "pv_visualizer.py"

    if mesh_path:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".vtk")
        tmp.close()
        convert_to_vtk(mesh_path, tmp.name)
        data_path = tmp.name
    elif nodes is not None and elements is not None:
        data_path = mesh_to_temp_vtk(nodes, elements)
    else:
        raise ValueError("mesh_path or nodes/elements must be provided")

    cmd = [
        "python",
        str(script),
        "--data",
        data_path,
        "--port",
        str(port),
        "--host",
        host,
    ]
    if verbose:
        cmd.append("--verbose")
    subprocess.Popen(cmd)
    return f"http://{host}:{port}/"


SDEA_LOGO_URL = (
    "https://sdeasolutions.com/wp-content/uploads/2021/11/"
    "cropped-SDEA_Logo-ORIGINAL-250x250-1.jpg"
)
OPENRADIOSS_LOGO_URL = (
    "https://openradioss.org/wp-content/uploads/2023/07/openradioss-logo.png"
)
ANSYS_LOGO_URL = "https://www.ansys.com/content/dam/company/brand/logos/ansys-logos/ansys-logo.svg"

from cdb2rad.parser import parse_cdb
from cdb2rad.writer_rad import (
    write_rad,
    DEFAULT_RUNNAME,
    DEFAULT_FINAL_TIME,
    DEFAULT_ANIM_DT,
    DEFAULT_HISTORY_DT,
    DEFAULT_DT_RATIO,
    DEFAULT_PRINT_N,
    DEFAULT_PRINT_LINE,
    DEFAULT_STOP_EMAX,
    DEFAULT_STOP_MMAX,
    DEFAULT_STOP_NMAX,
    DEFAULT_STOP_NTH,
    DEFAULT_STOP_NANIM,
    DEFAULT_STOP_NERR,
    DEFAULT_THICKNESS,
)
from cdb2rad.writer_inc import write_mesh_inc
from cdb2rad.rad_validator import validate_rad_format
from cdb2rad.utils import check_rad_inputs
from cdb2rad.remote import add_remote_point, next_free_node_id
from cdb2rad.pdf_search import (
    REFERENCE_GUIDE_URL,
    THEORY_MANUAL_URL,
    USER_GUIDE as USER_GUIDE_URL,
)

MAX_EDGES = 10000
MAX_FACES = 15000

# Mappings for dropdown labels with short explanations
LAW_DESCRIPTIONS = {
    "LAW1": "Elástico lineal",
    "LAW2": "Modelo Johnson-Cook",
    "LAW27": "Modelo plástico isotrópico",
    "LAW36": "Modelo material avanzado",
    "LAW44": "Modelo Cowper-Symonds",
}

FAIL_DESCRIPTIONS = {
    "": "Sin criterio de fallo",
    "JOHNSON": "Johnson-Cook failure",
    "BIQUAD": "Criterio Biquadrático",
    "TAB1": "Fallo tabulado",
}

BC_DESCRIPTIONS = {
    "BCS": "Condición fija",
    "PRESCRIBED_MOTION": "Movimiento prescrito",
}

INT_DESCRIPTIONS = {
    "TYPE2": "Nodo-superficie",
    "TYPE7": "Superficie-superficie",
}


# Units to display for each parameter depending on the selected system
UNIT_OPTIONS = ["SI", "Imperial"]

PARAM_UNITS = {
    "Densidad": {"SI": "kg/m3", "Imperial": "lb/in3"},
    "E": {"SI": "MPa", "Imperial": "psi"},
    "A": {"SI": "MPa", "Imperial": "psi"},
    "B": {"SI": "MPa", "Imperial": "psi"},
    "SIG0": {"SI": "MPa", "Imperial": "psi"},
    "SU": {"SI": "MPa", "Imperial": "psi"},
    "Tiempo final": {"SI": "s", "Imperial": "s"},
    "Paso animación": {"SI": "s", "Imperial": "s"},
    "Intervalo historial": {"SI": "s", "Imperial": "s"},
    "Gap": {"SI": "mm", "Imperial": "in"},
    "Stiffness": {"SI": "N/mm", "Imperial": "lbf/in"},
    "Vx": {"SI": "m/s", "Imperial": "ft/s"},
    "Vy": {"SI": "m/s", "Imperial": "ft/s"},
    "Vz": {"SI": "m/s", "Imperial": "ft/s"},
    "g": {"SI": "m/s²", "Imperial": "ft/s²"},
}


def label_with_unit(base: str) -> str:
    unit_sys = st.session_state.get("unit_sys", UNIT_OPTIONS[0])
    unit = PARAM_UNITS.get(base, {}).get(unit_sys)
    return f"{base} ({unit})" if unit else base

def input_with_help(label: str, value: float, key: str):
    """Simplified numeric input without additional help."""
    return st.number_input(label_with_unit(label), value=value, key=key)


def viewer_html(

    nodes: Dict[int, List[float]],
    elements: List[Tuple[int, int, List[int]]],
    selected_eids: Optional[Set[int]] = None,
    max_edges: int = MAX_EDGES,
    max_faces: int = MAX_FACES,
) -> str:
    """Return an HTML snippet with a lightweight Three.js mesh viewer.

    ``selected_eids`` may filter the elements to display. A subset of
    ``max_edges`` edges and ``max_faces`` triangular faces is used when the
    mesh is large to keep the browser responsive.
    """

    if selected_eids:
        elements = [e for e in elements if e[0] in selected_eids]

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
<script src='https://cdn.jsdelivr.net/npm/three@0.154.0/examples/jsm/controls/OrbitControls.js'></script>
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
.app-title {{
    text-align: center;
    color: {SDEA_ORANGE};
    font-size: 2.5em;
    margin-bottom: 0.2em;
}}
</style>
"""
st.markdown(style, unsafe_allow_html=True)

st.markdown(
    "<h1 class='app-title'>\u2728 CDB2Rad Dashboard v0.0</h1>",
    unsafe_allow_html=True,
)

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

unit_sel = st.selectbox(
    "Sistema de unidades",
    UNIT_OPTIONS,
    key="unit_sys",
)

uploaded = st.file_uploader("Subir archivo .cdb", type="cdb")

file_path = None
if uploaded is not None:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".cdb")
    tmp.write(uploaded.getvalue())
    tmp.close()
    file_path = tmp.name

if file_path:
    work_dir = st.text_input(
        "Directorio de trabajo",
        value=st.session_state.get("work_dir", str(Path.cwd())),
    )
    st.session_state["work_dir"] = work_dir

    if "parts" not in st.session_state:
        st.session_state["parts"] = []
    nodes, elements, node_sets, elem_sets, materials = load_cdb(file_path)

    info_tab, preview_tab, vtk_tab, inp_tab, rad_tab, help_tab = st.tabs(
        [
            "Información",
            "Vista 3D",
            "Generar VTK",

            "Generar INC",
            "Generar RAD",
            "Ayuda",
        ]
    )

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
        all_elem_sets = {**elem_sets, **st.session_state.get("subsets", {})}
        st.write("Conjuntos de elementos:", len(all_elem_sets))
        for name, eids in all_elem_sets.items():
            st.write(f"- {name}: {len(eids)} elementos")
        if st.session_state["parts"]:
            st.write("Partes definidas:")
            for part in st.session_state["parts"]:
                st.write(f"- {part['name']} (ID {part['id']}) → {part['set']}")
        st.write("Materiales:")
        for mid, props in materials.items():
            st.write(f"- ID {mid}: {props}")

    with preview_tab:
        port = st.number_input("Puerto ParaView Web", value=8080, step=1)
        cmd = (
            f"\"C:\\Program Files\\ParaView 5.12.0\\bin\\pvpython.exe\" "
            f"-m paraview.apps.visualizer --data \"C:\\JAVIER\\OPEN_RADIOSS\\paraview\\data\" "
            f"--content \"C:\\JAVIER\\OPEN_RADIOSS\\paraview\\www\" --port {int(port)}"
        )
        st.text_input("Comando para lanzar", value=cmd, key="pv_cmd")
        if st.button("Visualizar con ParaView Web"):
            url = launch_paraview_server(
                nodes=nodes,
                elements=elements,
                port=int(port),
                verbose=True,
            )
            st.session_state["pvw_url"] = url
        if "pvw_url" in st.session_state:
            st.components.v1.html(
                f'<iframe src="{st.session_state["pvw_url"]}" '
                'style="width:100%;height:600px;border:none;"></iframe>',
                height=620,
            )

    with vtk_tab:
        st.subheader("Exportar VTK")
        vtk_dir = st.text_input(
            "Directorio de salida",
            value=st.session_state.get("work_dir", str(Path.cwd())),
            key="vtk_dir",
        )
        vtk_name = st.text_input("Nombre de archivo", value="mesh", key="vtk_name")
        vtk_format = st.selectbox("Formato", [".vtk", ".vtp"], key="vtk_format")
        overwrite_vtk = st.checkbox("Sobrescribir si existe", value=False, key="overwrite_vtk")
        if st.button("Generar VTK"):
            out_dir = Path(vtk_dir).expanduser()
            out_dir.mkdir(parents=True, exist_ok=True)
            vtk_path = out_dir / f"{vtk_name}{vtk_format}"
            if vtk_path.exists() and not overwrite_vtk:
                st.error("El archivo ya existe. Elija otro nombre o active sobrescribir")
            else:
                if vtk_format == ".vtp":
                    write_vtp(nodes, elements, str(vtk_path))
                else:
                    write_vtk(nodes, elements, str(vtk_path))
                st.success(f"Archivo guardado en: {vtk_path}")


    with settings_tab:
        st.subheader("Configuración de propiedades")
        if "properties" not in st.session_state:
            st.session_state["properties"] = []
        if "parts" not in st.session_state:
            st.session_state["parts"] = []

        with st.expander("Definir propiedad"):
            pid = st.number_input("ID propiedad", value=len(st.session_state["properties"]) + 1, key="prop_id")
            pname = st.text_input("Nombre", value=f"PROP_{pid}", key="prop_name")
            ptype = st.selectbox("Tipo", ["SHELL", "SOLID"], key="prop_type")
            if ptype == "SHELL":
                thick = st.number_input("Espesor", value=DEFAULT_THICKNESS, key="prop_thick")
            else:
                thick = None
            if st.button("Añadir propiedad"):
                data = {"id": int(pid), "name": pname, "type": ptype}
                if thick is not None:
                    data["thickness"] = thick
                st.session_state["properties"].append(data)

        if st.session_state["properties"]:
            st.write("Propiedades definidas:")
            for i, pr in enumerate(st.session_state["properties"]):
                cols = st.columns([4, 1])
                with cols[0]:
                    st.json(pr)
                with cols[1]:
                    if st.button("Eliminar", key=f"del_prop_{i}"):
                        st.session_state["properties"].pop(i)
                        _rerun()

        with st.expander("Definir parte"):
            part_id = st.number_input("ID parte", value=len(st.session_state["parts"]) + 1, key="part_id")
            part_name = st.text_input("Nombre parte", value=f"PART_{part_id}", key="part_name")
            prop_opts = [p["id"] for p in st.session_state["properties"]]
            pid_sel = st.selectbox("Propiedad", prop_opts, disabled=not prop_opts, key="part_pid")
            mid_sel = st.number_input("Material ID", value=1, key="part_mid")
            if st.button("Añadir parte"):
                st.session_state["parts"].append({
                    "id": int(part_id),
                    "name": part_name,
                    "pid": int(pid_sel) if prop_opts else 1,
                    "mid": int(mid_sel),
                })

        if st.session_state["parts"]:
            st.write("Partes definidas:")
            for i, pt in enumerate(st.session_state["parts"]):
                cols = st.columns([4, 1])
                with cols[0]:
                    st.json(pt)
                with cols[1]:
                    if st.button("Eliminar", key=f"del_part_{i}"):
                        st.session_state["parts"].pop(i)
                        _rerun()

    with inp_tab:
        st.subheader("Generar mesh.inc")

        use_sets = st.checkbox("Incluir name selections", value=True)
        use_mats = st.checkbox("Incluir materiales", value=True)
        inc_dir = st.text_input(
            "Directorio de salida",
            value=st.session_state.get("work_dir", str(Path.cwd())),
            key="inc_dir",
        )
        inc_name = st.text_input(
            "Nombre de archivo", value="mesh", key="inc_name"
        )
        overwrite_inc = st.checkbox("Sobrescribir si existe", value=False, key="overwrite_inc")

        if st.button("Generar .inc"):
            out_dir = Path(inc_dir).expanduser()
            out_dir.mkdir(parents=True, exist_ok=True)
            inp_path = out_dir / f"{inc_name}.inc"
            if inp_path.exists() and not overwrite_inc:
                st.error("El archivo ya existe. Elija otro nombre o directorio")
            else:
                all_elem_sets = {**elem_sets, **st.session_state.get("subsets", {})}
                write_mesh_inc(
                    nodes,
                    elements,
                    str(inp_path),
                    node_sets=node_sets if use_sets else None,
                    elem_sets=all_elem_sets if use_sets else None,
                    materials=materials if use_mats else None,
                )
                st.success(f"Fichero generado en: {inp_path}")
                with st.expander("Ver .inc completo"):
                    st.text_area(
                        "mesh.inc", inp_path.read_text(), height=400
                    )

    with rad_tab:
        st.subheader("Generar RAD")
        include_inc = st.checkbox(
            "Incluir línea #include mesh.inc",
            value=True,
            key="include_inc_rad",
        )

        if "impact_materials" not in st.session_state:
            st.session_state["impact_materials"] = []
        if "bcs" not in st.session_state:
            st.session_state["bcs"] = []
        if "interfaces" not in st.session_state:
            st.session_state["interfaces"] = []
        if "next_inter_idx" not in st.session_state:
            st.session_state["next_inter_idx"] = 1
        if "init_vel" not in st.session_state:
            st.session_state["init_vel"] = None
        if "gravity" not in st.session_state:
            st.session_state["gravity"] = None
        if "control_settings" not in st.session_state:
            st.session_state["control_settings"] = None
        if "rbodies" not in st.session_state:
            st.session_state["rbodies"] = []
        if "rbe2" not in st.session_state:
            st.session_state["rbe2"] = []
        if "rbe3" not in st.session_state:
            st.session_state["rbe3"] = []
        if "remote_points" not in st.session_state:
            st.session_state["remote_points"] = []

        if "properties" not in st.session_state:
            st.session_state["properties"] = []
        if "parts" not in st.session_state:
            st.session_state["parts"] = []


        extra_nodes = {
            rp["id"]: list(rp["coords"])
            for rp in st.session_state["remote_points"]
        }
        all_nodes = {**nodes, **extra_nodes}
        extra_sets = {
            f"REMOTE_{rp['id']}": [rp['id']] for rp in st.session_state["remote_points"]
        }
        all_node_sets = {**node_sets, **extra_sets}
        all_elem_sets = {**elem_sets, **st.session_state["subsets"]}

        part_node_sets = {}
        for part in st.session_state["parts"]:
            set_name = part.get("set")
            eids = all_elem_sets.get(set_name, [])
            nodes_in_part = {nid for eid, _et, ns in elements if eid in eids for nid in ns}
            if nodes_in_part:
                part_node_sets[part["name"]] = sorted(nodes_in_part)

        all_node_sets.update(part_node_sets)

        with st.expander("Definición de materiales"):
            use_cdb_mats = st.checkbox("Incluir materiales del CDB", value=False)
            # Desactivado por defecto para evitar añadir tarjetas vacías
            use_impact = st.checkbox(
                "Incluir materiales de impacto", value=False
            )

            if use_impact:
                with st.expander("Materiales de impacto"):
                    mat_id = input_with_help(
                        "ID material",
                        len(st.session_state["impact_materials"]) + 1,
                        "mat_id",
                    )
                    law = st.selectbox(
                        "Tipo",
                        list(LAW_DESCRIPTIONS.keys()),
                        format_func=lambda k: f"{k} - {LAW_DESCRIPTIONS[k]}",
                    )
                    dens_i = input_with_help("Densidad", 7800.0, "dens_i")
                    e_i = input_with_help("E", 210000.0, "e_i")
                    nu_i = input_with_help("Poisson", 0.3, "nu_i")
                    extra: Dict[str, float] = {}
                    if law == "LAW2":
                        extra["A"] = input_with_help("A", 200.0, "a_i")
                        extra["B"] = input_with_help("B", 400.0, "b_i")
                        extra["N"] = input_with_help("N", 0.5, "n_i")
                        extra["C"] = input_with_help("C", 0.01, "c_i")
                        extra["EPS0"] = input_with_help("EPS0", 1.0, "eps0_i")
                    elif law == "LAW27":
                        extra["SIG0"] = input_with_help("SIG0", 200.0, "sig0")
                        extra["SU"] = input_with_help("SU", 0.0, "su")
                        extra["EPSU"] = input_with_help("EPSU", 0.0, "epsu")
                    elif law == "LAW36":
                        extra["Fsmooth"] = input_with_help("Fsmooth", 0.0, "fs")
                        extra["Fcut"] = input_with_help("Fcut", 0.0, "fc")
                        extra["Chard"] = input_with_help("Chard", 0.0, "ch")
                    elif law == "LAW44":
                        extra["A"] = input_with_help("A", 0.0, "cow_a")
                        extra["B"] = input_with_help("B", 0.0, "cow_b")
                        extra["N"] = input_with_help("N", 1.0, "cow_n")
                        extra["C"] = input_with_help("C", 0.0, "cow_c")

                    fail_type = st.selectbox(
                        "Modo de fallo",
                        list(FAIL_DESCRIPTIONS.keys()),
                        format_func=lambda k: "Ninguno" if k == "" else f"FAIL/{k} - {FAIL_DESCRIPTIONS[k]}",
                    )
                    fail_params: Dict[str, float] = {}
                    if fail_type:
                        if fail_type == "JOHNSON":
                            fail_params["D1"] = input_with_help("D1", 0.0, "d1")
                            fail_params["D2"] = input_with_help("D2", 0.0, "d2")
                            fail_params["D3"] = input_with_help("D3", 0.0, "d3")
                            fail_params["D4"] = input_with_help("D4", 0.0, "d4")
                            fail_params["D5"] = input_with_help("D5", 0.0, "d5")
                        elif fail_type == "BIQUAD":
                            fail_params["C1"] = input_with_help("C1", 0.0, "c1")
                            fail_params["C2"] = input_with_help("C2", 0.0, "c2")
                            fail_params["C3"] = input_with_help("C3", 0.0, "c3")
                        elif fail_type == "TAB1":
                            fail_params["Dcrit"] = input_with_help("Dcrit", 1.0, "dcrit")

                    if st.button("Añadir material"):
                        data = {
                            "id": int(mat_id),
                            "LAW": law,
                            "EX": e_i,
                            "NUXY": nu_i,
                            "DENS": dens_i,
                        }
                        data.update(extra)
                        if fail_type:
                            data["FAIL"] = {"TYPE": fail_type, **fail_params}
                        st.session_state["impact_materials"].append(data)

                    if st.session_state["impact_materials"]:
                        st.write("Materiales definidos:")
                        for i, mat in enumerate(st.session_state["impact_materials"]):
                            cols = st.columns([4, 1])
                            with cols[0]:
                                st.json(mat)
                            with cols[1]:
                                if st.button("Eliminar", key=f"del_mat_{i}"):
                                    st.session_state["impact_materials"].pop(i)
                                    _rerun()

        with st.expander("Bloques (/PART y /SUBSET)"):
            with st.expander("/SUBSET"):
                sub_name = st.text_input("Nombre subset", key="sub_name")
                base_sets = st.multiselect(
                    "Conjuntos base", list(all_elem_sets.keys()), key="sub_sets"
                )
                manual = st.text_area("IDs manuales", key="sub_ids")
                if st.button("Añadir subset") and sub_name:
                    ids = set()
                    for s in base_sets:
                        ids.update(all_elem_sets.get(s, []))
                    for tok in manual.replace(',', ' ').split():
                        try:
                            ids.add(int(tok))
                        except ValueError:
                            pass
                    if ids:
                        st.session_state["subsets"][sub_name] = sorted(ids)
                        _rerun()
            for name, ids in st.session_state["subsets"].items():
                cols = st.columns([4, 1])
                with cols[0]:
                    st.write(f"{name}: {len(ids)} elementos")
                with cols[1]:
                    if st.button("Eliminar", key=f"del_subset_{name}"):
                        del st.session_state["subsets"][name]
                        _rerun()

            with st.expander("/PART"):
                pid = st.number_input("ID", 1, key="part_id")
                pname = st.text_input("Nombre part", key="part_name")
                sel_set = st.selectbox(
                    "Subset o conjunto", list(all_elem_sets.keys()), key="part_set", disabled=not all_elem_sets
                )
                mat_pid = st.number_input("Material ID", 1, key="part_mat")
                if st.button("Añadir part") and pname and sel_set:
                    st.session_state["parts"].append({
                        "id": int(pid),
                        "name": pname,
                        "set": sel_set,
                        "mat": int(mat_pid),
                    })
                    _rerun()
            for i, part in enumerate(st.session_state["parts"]):
                cols = st.columns([4, 1])
                with cols[0]:
                    st.write(f"{part['name']} → {part['set']} (ID {part['id']})")
                with cols[1]:
                    if st.button("Eliminar", key=f"del_part_{i}"):
                        st.session_state["parts"].pop(i)
                        _rerun()


        with st.expander("Control del cálculo"):
            runname = st.text_input(
                "Nombre de la simulación", value=DEFAULT_RUNNAME
            )
            t_end = input_with_help("Tiempo final", DEFAULT_FINAL_TIME, "t_end")
            if st.checkbox("Definir paso animación", key="en_anim"):
                anim_dt = input_with_help("Paso animación", DEFAULT_ANIM_DT, "anim_dt")
            else:
                anim_dt = None
            if st.checkbox("Definir intervalo historial", key="en_tfile"):
                tfile_dt = input_with_help("Intervalo historial", DEFAULT_HISTORY_DT, "tfile_dt")
            else:
                tfile_dt = None
            if st.checkbox("Definir factor seguridad DT", key="en_dt"):
                dt_ratio = input_with_help(
                    "Factor seguridad DT",
                    DEFAULT_DT_RATIO,
                    "dt_ratio",
                )
            else:
                dt_ratio = None
            adv_enabled = st.checkbox("Activar opciones avanzadas")
            if adv_enabled:
                st.markdown("### Opciones avanzadas")
                if st.checkbox("Definir /PRINT", key="en_print"):
                    print_n = input_with_help("PRINT cada n ciclos", DEFAULT_PRINT_N, "print_n")
                    print_line = input_with_help("Línea cabecera", DEFAULT_PRINT_LINE, "print_line")
                else:
                    print_n = None
                    print_line = None
                rfile_cycle = input_with_help("Ciclos entre RFILE", 0, "rfile_cycle")
                rfile_n = input_with_help("Número de RFILE", 0, "rfile_n")
                h3d_dt = input_with_help("Paso H3D", 0.0, "h3d_dt")
                col1, col2, col3 = st.columns(3)
                with col1:
                    stop_emax = input_with_help("Emax", DEFAULT_STOP_EMAX, "stop_emax")
                with col2:
                    stop_mmax = input_with_help("Mmax", DEFAULT_STOP_MMAX, "stop_mmax")
                with col3:
                    stop_nmax = input_with_help("Nmax", DEFAULT_STOP_NMAX, "stop_nmax")
                col4, col5, col6 = st.columns(3)
                with col4:
                    stop_nth = input_with_help("NTH", DEFAULT_STOP_NTH, "stop_nth")
                with col5:
                    stop_nanim = input_with_help("NANIM", DEFAULT_STOP_NANIM, "stop_nanim")
                with col6:
                    stop_nerr = input_with_help("NERR_POSIT", DEFAULT_STOP_NERR, "stop_nerr")
                adyrel_start = input_with_help("ADYREL inicio", 0.0, "adyrel_start")
                adyrel_stop = input_with_help("ADYREL fin", 0.0, "adyrel_stop")
            else:
                print_n = None
                print_line = None
                rfile_cycle = 0
                rfile_n = 0
                h3d_dt = 0.0
                stop_emax = DEFAULT_STOP_EMAX
                stop_mmax = DEFAULT_STOP_MMAX
                stop_nmax = DEFAULT_STOP_NMAX
                stop_nth = DEFAULT_STOP_NTH
                stop_nanim = DEFAULT_STOP_NANIM
                stop_nerr = DEFAULT_STOP_NERR
                adyrel_start = None
                adyrel_stop = None

            if st.button("Añadir control"):
                st.session_state["control_settings"] = {
                    "runname": runname,
                    "t_end": t_end,
                    "anim_dt": anim_dt,
                    "tfile_dt": tfile_dt,
                    "dt_ratio": dt_ratio,
                    "print_n": int(print_n) if print_n is not None else None,
                    "print_line": int(print_line) if print_line is not None else None,
                    "rfile_cycle": int(rfile_cycle) if rfile_cycle else None,
                    "rfile_n": int(rfile_n) if rfile_n else None,
                    "h3d_dt": h3d_dt if h3d_dt > 0 else None,
                    "stop_emax": stop_emax,
                    "stop_mmax": stop_mmax,
                    "stop_nmax": stop_nmax,
                    "stop_nth": int(stop_nth),
                    "stop_nanim": int(stop_nanim),
                    "stop_nerr": int(stop_nerr),
                    "adyrel_start": adyrel_start,
                    "adyrel_stop": adyrel_stop,
                }
            if st.session_state["control_settings"]:
                st.write("Control de cálculo definido:")
                cols = st.columns([4, 1])
                with cols[0]:
                    st.json(st.session_state["control_settings"])
                with cols[1]:
                    if st.button("Eliminar", key="del_ctrl"):
                        st.session_state["control_settings"] = None
                        _rerun()

        with st.expander("Condiciones de contorno (BCS)"):
            bc_name = st.text_input("Nombre BC", value="Fixed")
            bc_type = st.selectbox(
                "Tipo BC",
                list(BC_DESCRIPTIONS.keys()),
                format_func=lambda k: f"{k} - {BC_DESCRIPTIONS[k]}",
            )
            bc_set = st.selectbox(
                "Conjunto de nodos",
                list(all_node_sets.keys()),
                disabled=not all_node_sets,
            )
            bc_data = {}
            if bc_type == "BCS":
                bc_tra = st.text_input("Traslación (111/000)", value="111")
                bc_rot = st.text_input("Rotación (111/000)", value="111")
                bc_data.update({"tra": bc_tra, "rot": bc_rot})
            else:
                bc_dir = input_with_help("Dirección", 1, "bc_dir")
                bc_val = input_with_help("Valor", 0.0, "bc_val")
                bc_data.update({"dir": int(bc_dir), "value": float(bc_val)})

            if st.button("Añadir BC") and bc_set:
                node_list = all_node_sets.get(bc_set, [])
                entry = {
                    "name": bc_name,
                    "type": bc_type,
                    "nodes": node_list,
                }
                entry.update(bc_data)
                st.session_state["bcs"].append(entry)

            for i, bc in enumerate(st.session_state["bcs"]):
                cols = st.columns([4, 1])
                with cols[0]:
                    st.json(bc)
                with cols[1]:
                    if st.button("Eliminar", key=f"del_bc_{i}"):
                        st.session_state["bcs"].pop(i)
                        _rerun()

        with st.expander("Puntos remotos"):
            colx, coly, colz = st.columns(3)
            with colx:
                rx = st.number_input("X", 0.0, key="rp_x")
            with coly:
                ry = st.number_input("Y", 0.0, key="rp_y")
            with colz:
                rz = st.number_input("Z", 0.0, key="rp_z")
            auto = st.checkbox("ID automático", value=True, key="rp_auto")
            next_id = next_free_node_id(all_nodes)
            rid = st.number_input("ID", value=next_id, key="rp_id", disabled=auto)
            if st.button("Añadir punto remoto"):
                try:
                    if auto:
                        _, nid = add_remote_point(all_nodes, (rx, ry, rz))
                    else:
                        _, nid = add_remote_point(all_nodes, (rx, ry, rz), int(rid))
                    st.session_state["remote_points"].append({"id": nid, "coords": (rx, ry, rz)})
                    _rerun()
                except ValueError as e:
                    st.error(str(e))
            for i, rp in enumerate(st.session_state.get("remote_points", [])):
                cols = st.columns([4, 1])
                with cols[0]:
                    st.write(f"ID {rp['id']} → {rp['coords']}")
                with cols[1]:
                    if st.button("Eliminar", key=f"del_rp_{i}"):
                        st.session_state["remote_points"].pop(i)
                        _rerun()

        with st.expander("Interacciones (INTER)"):
            int_type = st.selectbox(
                "Tipo",
                list(INT_DESCRIPTIONS.keys()),
                key="itf_type",
                format_func=lambda k: f"{k} - {INT_DESCRIPTIONS[k]}",
            )
            idx = st.session_state.get("next_inter_idx", 1)
            def_name = f"{int_type}_{idx}"
            int_name = st.text_input(
                "Nombre interfaz",
                value=st.session_state.get("int_name", def_name),
                key="int_name",
            )
            slave_set = st.selectbox(
                "Conjunto esclavo",
                list(all_node_sets.keys()),
                key="slave_set",
                disabled=not all_node_sets,
            )
            master_set = st.selectbox(
                "Conjunto maestro",
                list(all_node_sets.keys()),
                key="master_set",
                disabled=not all_node_sets,
            )
            fric = input_with_help("Fricción", 0.0, "fric")

            gap = stiff = igap = None
            if int_type == "TYPE7":
                gap = input_with_help("Gap", 0.0, "gap")
                stiff = input_with_help("Stiffness", 0.0, "stiff")
                igap = input_with_help("Igap", 0, "igap")

            if st.button("Añadir interfaz") and slave_set and master_set:
                s_list = all_node_sets.get(slave_set, [])
                m_list = all_node_sets.get(master_set, [])
                if s_list and m_list:
                    itf = {
                        "type": int_type,
                        "name": int_name,
                        "slave": s_list,
                        "master": m_list,
                        "fric": float(fric),
                    }
                    if int_type == "TYPE7":
                        itf.update({
                            "gap": gap,
                            "stiff": stiff,
                            "igap": int(igap),
                        })
                    st.session_state["interfaces"].append(itf)
                    st.session_state["next_inter_idx"] += 1
                    st.session_state["int_name"] = f"{int_type}_{st.session_state['next_inter_idx']}"
                    _rerun()
            for i, itf in enumerate(st.session_state["interfaces"]):
                cols = st.columns([4, 1])
                with cols[0]:
                    st.json(itf)
                with cols[1]:
                    if st.button("Eliminar", key=f"del_itf_{i}"):
                        st.session_state["interfaces"].pop(i)
                        _rerun()

        with st.expander("Rigid Connectors"):
            with st.expander("/RBODY"):
                rb_id = st.number_input("RBID", 1)
                master = st.selectbox("Nodo maestro", list(all_nodes.keys()), key="rbody_master")
                slaves = st.multiselect("Nodos secundarios", list(all_nodes.keys()), key="rb_slaves")
                slave_sets = st.multiselect(
                    "Name selections", list(all_node_sets.keys()), key="rb_sets", disabled=not all_node_sets
                )
                if st.button("Añadir RBODY"):
                    nodes_union = {int(n) for n in slaves}
                    for s in slave_sets:
                        nodes_union.update(all_node_sets.get(s, []))
                    st.session_state["rbodies"].append({
                        "RBID": int(rb_id),
                        "Gnod_id": int(master),
                        "nodes": sorted(nodes_union),
                    })
            for i, rb in enumerate(st.session_state.get("rbodies", [])):
                cols = st.columns([4, 1])
                with cols[0]:
                    st.json(rb)
                with cols[1]:
                    if st.button("Eliminar", key=f"del_rb_{i}"):
                        st.session_state["rbodies"].pop(i)
                        _rerun()

            with st.expander("/RBE2"):
                m = st.selectbox("Master", list(all_nodes.keys()), key="rbe2m")
                slaves2 = st.multiselect("Slaves", list(all_nodes.keys()), key="rbe2s")
                slave_sets2 = st.multiselect(
                    "Name selections", list(all_node_sets.keys()), key="rbe2_sets", disabled=not all_node_sets
                )
                if st.button("Añadir RBE2"):
                    nodes_union = {int(n) for n in slaves2}
                    for s in slave_sets2:
                        nodes_union.update(all_node_sets.get(s, []))
                    st.session_state["rbe2"].append({
                        "N_master": int(m),
                        "N_slave_list": sorted(nodes_union),
                    })
            for i, rb in enumerate(st.session_state.get("rbe2", [])):
                cols = st.columns([4, 1])
                with cols[0]:
                    st.json(rb)
                with cols[1]:
                    if st.button("Eliminar", key=f"del_rbe2_{i}"):
                        st.session_state["rbe2"].pop(i)
                        _rerun()

            with st.expander("/RBE3"):
                dep = st.selectbox("Dependiente", list(all_nodes.keys()), key="rbe3d")
                indep_nodes = st.multiselect("Independientes", list(all_nodes.keys()), key="rbe3i")
                indep_sets = st.multiselect(
                    "Name selections", list(all_node_sets.keys()), key="rbe3_sets", disabled=not all_node_sets
                )
                if st.button("Añadir RBE3"):
                    nodes_union = {int(n) for n in indep_nodes}
                    for s in indep_sets:
                        nodes_union.update(all_node_sets.get(s, []))
                    st.session_state["rbe3"].append({
                        "N_dependent": int(dep),
                        "independent": [(nid, 1.0) for nid in sorted(nodes_union)],
                    })
            for i, rb in enumerate(st.session_state.get("rbe3", [])):
                cols = st.columns([4, 1])
                with cols[0]:
                    st.json(rb)
                with cols[1]:
                    if st.button("Eliminar", key=f"del_rbe3_{i}"):
                        st.session_state["rbe3"].pop(i)
                        _rerun()

        with st.expander("Velocidad inicial (IMPVEL)"):
            vel_set = st.selectbox(
                "Conjunto de nodos",
                list(all_node_sets.keys()),
                key="vel_set",
                disabled=not all_node_sets,
            )
            vx = input_with_help("Vx", 0.0, "vx")
            vy = input_with_help("Vy", 0.0, "vy")
            vz = input_with_help("Vz", 0.0, "vz")
            if st.button("Asignar velocidad") and vel_set:
                n_list = all_node_sets.get(vel_set, [])
                st.session_state["init_vel"] = {
                    "nodes": n_list,
                    "vx": vx,
                    "vy": vy,
                    "vz": vz,
                }
            if st.session_state["init_vel"]:
                cols = st.columns([4, 1])
                with cols[0]:
                    st.json(st.session_state["init_vel"])
                with cols[1]:
                    if st.button("Eliminar", key="del_initvel"):
                        st.session_state["init_vel"] = None
                        _rerun()

        with st.expander("Carga de gravedad (GRAVITY)"):
            g = input_with_help("g", 9.81, "grav_g")
            nx = input_with_help("nx", 0.0, "grav_nx")
            ny = input_with_help("ny", 0.0, "grav_ny")
            nz = input_with_help("nz", -1.0, "grav_nz")
            comp = input_with_help("Componente", 3, "grav_comp")
            if st.button("Asignar gravedad"):
                st.session_state["gravity"] = {
                    "g": g,
                    "nx": nx,
                    "ny": ny,
                    "nz": nz,
                    "comp": int(comp),
                }
            if st.session_state["gravity"]:
                cols = st.columns([4, 1])
                with cols[0]:
                    st.json(st.session_state["gravity"])
                with cols[1]:
                    if st.button("Eliminar", key="del_gravity"):
                        st.session_state["gravity"] = None
                        _rerun()


        rad_dir = st.text_input(
            "Directorio de salida",
            value=st.session_state.get("work_dir", str(Path.cwd())),
            key="rad_dir",
        )
        rad_name = st.text_input(
            "Nombre de archivo RAD", value="model_0000", key="rad_name"
        )
        overwrite_rad = st.checkbox("Sobrescribir si existe", value=False, key="overwrite_rad")

        if st.button("Chequear configuracion"):
            errs = check_rad_inputs(
                use_cdb_mats,
                materials,
                use_impact,
                st.session_state.get("impact_materials"),
                st.session_state.get("bcs"),
                st.session_state.get("interfaces"),
            )
            if errs:
                for e in errs:
                    st.error(e)
            else:
                st.success("Configuracion OK")


        if st.button("Generar .rad"):
            out_dir = Path(rad_dir).expanduser()
            out_dir.mkdir(parents=True, exist_ok=True)
            rad_path = out_dir / f"{rad_name}.rad"
            mesh_path = out_dir / "mesh.inc"
            impact_defined = use_impact and st.session_state.get("impact_materials")
            if (rad_path.exists() or mesh_path.exists()) and not overwrite_rad:
                st.error("El archivo ya existe. Elija otro nombre o directorio")
            else:
                extra = None
                if use_impact and st.session_state["impact_materials"]:
                        extra = {
                            m["id"]: {k: v for k, v in m.items() if k != "id"}
                            for m in st.session_state["impact_materials"]
                        }
                ctrl = st.session_state.get("control_settings")
                if ctrl:
                    runname = ctrl.get("runname", runname)
                    t_end = ctrl.get("t_end", t_end)
                    anim_dt = ctrl.get("anim_dt", anim_dt)
                    tfile_dt = ctrl.get("tfile_dt", tfile_dt)
                    dt_ratio = ctrl.get("dt_ratio", dt_ratio)
                    print_n = ctrl.get("print_n", print_n)
                    print_line = ctrl.get("print_line", print_line)
                    rfile_cycle = ctrl.get("rfile_cycle", rfile_cycle)
                    rfile_n = ctrl.get("rfile_n", rfile_n)
                    h3d_dt = ctrl.get("h3d_dt", h3d_dt)
                    stop_emax = ctrl.get("stop_emax", stop_emax)
                    stop_mmax = ctrl.get("stop_mmax", stop_mmax)
                    stop_nmax = ctrl.get("stop_nmax", stop_nmax)
                    stop_nth = ctrl.get("stop_nth", stop_nth)
                    stop_nanim = ctrl.get("stop_nanim", stop_nanim)
                    stop_nerr = ctrl.get("stop_nerr", stop_nerr)
                    adyrel_start = ctrl.get("adyrel_start", adyrel_start)
                    adyrel_stop = ctrl.get("adyrel_stop", adyrel_stop)
                if not include_inc:
                    write_mesh_inc(all_nodes, elements, str(mesh_path), node_sets=all_node_sets)
                all_elem_sets = {**elem_sets, **st.session_state.get("subsets", {})}
                write_rad(
                        all_nodes,
                        elements,
                        str(rad_path),
                        mesh_inc=str(mesh_path),
                        include_inc=include_inc,
                        node_sets=all_node_sets,
                        elem_sets=all_elem_sets,
                        materials=materials if use_cdb_mats else None,
                        extra_materials=extra,

                        runname=runname,
                        t_end=t_end,
                        anim_dt=anim_dt,
                        tfile_dt=tfile_dt,
                        dt_ratio=dt_ratio,
                        print_n=int(print_n) if print_n is not None else None,
                        print_line=int(print_line) if print_line is not None else None,
                        rfile_cycle=int(rfile_cycle) if rfile_cycle else None,
                        rfile_n=int(rfile_n) if rfile_n else None,
                        h3d_dt=h3d_dt if h3d_dt > 0 else None,
                        stop_emax=stop_emax,
                        stop_mmax=stop_mmax,
                        stop_nmax=stop_nmax,
                        stop_nth=int(stop_nth),
                        stop_nanim=int(stop_nanim),
                        stop_nerr=int(stop_nerr),
                        adyrel=(adyrel_start, adyrel_stop),

                        boundary_conditions=st.session_state.get("bcs"),
                        interfaces=st.session_state.get("interfaces"),
                        rbody=st.session_state.get("rbodies"),
                        rbe2=st.session_state.get("rbe2"),
                        rbe3=st.session_state.get("rbe3"),
                        init_velocity=st.session_state.get("init_vel"),
                        gravity=st.session_state.get("gravity"),
                        properties=st.session_state.get("properties"),
                        parts=st.session_state.get("parts"),
                    )
                try:
                    validate_rad_format(str(rad_path))
                    st.info("Formato RAD OK")
                except ValueError as e:
                    st.error(f"Error formato: {e}")
                st.success(f"Ficheros generados en: {rad_path}")
                with st.expander("Ver .rad completo"):
                    st.text_area(
                        "model.rad", rad_path.read_text(), height=400
                    )

    with help_tab:
        st.subheader("Documentación")
        st.markdown(
            f"[Reference Guide]({REFERENCE_GUIDE_URL}) | "
            f"[User Guide]({USER_GUIDE_URL}) | "
            f"[Theory Manual]({THEORY_MANUAL_URL})"
        )

else:
    st.info("Sube un archivo .cdb")
