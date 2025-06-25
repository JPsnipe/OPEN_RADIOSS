import tempfile
from pathlib import Path
import sys
import json
import math
from typing import Dict, List, Tuple, Optional, Set

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
)
from cdb2rad.writer_inc import write_mesh_inc
from cdb2rad.pdf_search import (
    REFERENCE_GUIDE,
    REFERENCE_GUIDE_URL,
    THEORY_MANUAL,

    USER_GUIDE,


    search_pdf,
)


MAX_EDGES = 10000
MAX_FACES = 15000

# Available unit systems (mass, length, time)
UNIT_SYSTEMS = {
    "kg-mm-s": ("kg", "mm", "s"),
    "kg-m-s": ("kg", "m", "s"),
    "g-mm-ms": ("g", "mm", "ms"),
}

# Mappings for dropdown labels with short explanations
LAW_DESCRIPTIONS = {
    "LAW1": "Elástico lineal",
    "LAW2": "Modelo Johnson-Cook",
    "LAW27": "Modelo plástico isotrópico",
    "LAW36": "Modelo material avanzado",
    "LAW44": "Modelo Cowper-Symonds",
}

FAIL_DESCRIPTIONS = {
    "Ninguno": "Sin criterio de fallo",
    "FAIL/JOHNSON": "Johnson-Cook failure",
    "FAIL/BIQUAD": "Criterio Biquadrático",
    "FAIL/TAB1": "Fallo tabulado",
}

BC_DESCRIPTIONS = {
    "BCS": "Condición fija",
    "PRESCRIBED_MOTION": "Movimiento prescrito",
}

INT_DESCRIPTIONS = {
    "TYPE2": "Nodo-superficie",
    "TYPE7": "Superficie-superficie",
}

# Basic help strings for material parameters
PARAM_INFO = {
    "A": "Par\u00e1metro A del modelo Johnson-Cook. Representa la resistencia a la deformaci\u00f3n inicial.",
    "B": "Par\u00e1metro B del modelo Johnson-Cook. Controla el endurecimiento por deformaci\u00f3n.",
    "N": "Exponente n del modelo Johnson-Cook. Define la curva de endurecimiento.",
    "C": "Coeficiente de sensibilidad a la velocidad en Johnson-Cook.",
    "EPS0": "Referencia de velocidad de deformaci\u00f3n en Johnson-Cook.",
}

def johnson_cook_curve(A: float, B: float, N: float):
    import numpy as np
    import matplotlib.pyplot as plt

    eps = np.linspace(0, 0.3, 100)
    stress = A + B * eps ** N
    fig, ax = plt.subplots(figsize=(4, 3))
    ax.plot(eps, stress)
    ax.set_xlabel("Deformaci\u00f3n pl\u00e1stica")
    ax.set_ylabel("Tensi\u00f3n equivalente")
    ax.grid(True)
    return fig

def input_with_help(label: str, value: float, key: str):
    col1, col2 = st.columns([1, 1])
    with col1:
        val = st.number_input(label, value=value, key=key)
    with col2:
        info = PARAM_INFO.get(label)
        if info:
            with st.expander(f"Info {label}"):
                st.write(info)
                A = st.session_state.get("a_i", 200.0)
                B = st.session_state.get("b_i", 400.0)
                N = st.session_state.get("n_i", 0.5)
                fig = johnson_cook_curve(A, B, N)
                st.pyplot(fig)
    return val


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
    nodes, elements, node_sets, elem_sets, materials = load_cdb(file_path)
    info_tab, preview_tab, inp_tab, rad_tab, help_tab = st.tabs([
        "Información",
        "Vista 3D",
        "Generar INC",
        "Generar RAD",
        "Ayuda",
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
        st.write("Selecciona conjuntos de elementos para visualizar:")
        selected_sets = st.multiselect(
            "Conjuntos", list(elem_sets.keys()), default=list(elem_sets.keys())
        )
        sel_eids = set()
        for name in selected_sets:
            sel_eids.update(elem_sets.get(name, []))

        html = viewer_html(nodes, elements, selected_eids=sel_eids if sel_eids else None)
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
                write_mesh_inc(
                    nodes,
                    elements,
                    str(inp_path),
                    node_sets=node_sets if use_sets else None,
                    elem_sets=elem_sets if use_sets else None,
                    materials=materials if use_mats else None,
                )
                st.success(f"Fichero generado en: {inp_path}")
                lines = inp_path.read_text().splitlines()[:20]
                st.code("\n".join(lines))

    with rad_tab:
        st.subheader("Generar RAD")

        unit_choice = st.selectbox(
            "Sistema de unidades",
            list(UNIT_SYSTEMS.keys()),
            key="unit_choice",
        )
        units = UNIT_SYSTEMS[unit_choice]

        if "impact_materials" not in st.session_state:
            st.session_state["impact_materials"] = []
        if "bcs" not in st.session_state:
            st.session_state["bcs"] = []
        if "interfaces" not in st.session_state:
            st.session_state["interfaces"] = []
        if "init_vel" not in st.session_state:
            st.session_state["init_vel"] = None
        if "gravity" not in st.session_state:
            st.session_state["gravity"] = None

        with st.expander("Definición de materiales"):
            use_cdb_mats = st.checkbox("Incluir materiales del CDB", value=False)
            use_impact = st.checkbox("Incluir materiales de impacto", value=True)

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
                    st.caption(LAW_DESCRIPTIONS[law])
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
                        format_func=lambda k: f"{k} - {FAIL_DESCRIPTIONS[k]}",
                    )
                    fail_params: Dict[str, float] = {}
                    if fail_type:
                        st.caption(FAIL_DESCRIPTIONS[fail_type])
                    if fail_type != "Ninguno":
                        if fail_type == "FAIL/JOHNSON":
                            fail_params["D1"] = input_with_help("D1", 0.0, "d1")
                            fail_params["D2"] = input_with_help("D2", 0.0, "d2")
                            fail_params["D3"] = input_with_help("D3", 0.0, "d3")
                            fail_params["D4"] = input_with_help("D4", 0.0, "d4")
                            fail_params["D5"] = input_with_help("D5", 0.0, "d5")
                        elif fail_type == "FAIL/BIQUAD":
                            fail_params["C1"] = input_with_help("C1", 0.0, "c1")
                            fail_params["C2"] = input_with_help("C2", 0.0, "c2")
                            fail_params["C3"] = input_with_help("C3", 0.0, "c3")
                        elif fail_type == "FAIL/TAB1":
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
                        if fail_type != "Ninguno":
                            data["FAIL"] = {"TYPE": fail_type, **fail_params}
                        st.session_state["impact_materials"].append(data)

                    if st.session_state["impact_materials"]:
                        st.write("Materiales definidos:")
                        for mat in st.session_state["impact_materials"]:
                            st.json(mat)


        with st.expander("Control del cálculo"):
            runname = st.text_input(
                "Nombre de la simulación", value=DEFAULT_RUNNAME
            )
            t_end = input_with_help(
                f"Tiempo final ({units[2]})",
                DEFAULT_FINAL_TIME,
                "t_end",
            )
            anim_dt = input_with_help(
                f"Paso animación ({units[2]})",
                DEFAULT_ANIM_DT,
                "anim_dt",
            )
            tfile_dt = input_with_help(
                f"Intervalo historial ({units[2]})",
                DEFAULT_HISTORY_DT,
                "tfile_dt",
            )
            dt_ratio = input_with_help(
                "Factor seguridad DT",
                DEFAULT_DT_RATIO,
                "dt_ratio",
            )
            adv_enabled = st.checkbox("Activar opciones avanzadas")
            if adv_enabled:
                st.markdown("### Opciones avanzadas")
                print_n = input_with_help("PRINT cada n ciclos", DEFAULT_PRINT_N, "print_n")
                print_line = input_with_help("Línea cabecera", DEFAULT_PRINT_LINE, "print_line")
                rfile_cycle = input_with_help("Ciclos entre RFILE", 0, "rfile_cycle")
                rfile_n = input_with_help("Número de RFILE", 0, "rfile_n")
                h3d_dt = input_with_help(
                    f"Paso H3D ({units[2]})",
                    0.0,
                    "h3d_dt",
                )
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
                adyrel_start = input_with_help(
                    f"ADYREL inicio ({units[2]})",
                    0.0,
                    "adyrel_start",
                )
                adyrel_stop = input_with_help(
                    f"ADYREL fin ({units[2]})",
                    0.0,
                    "adyrel_stop",
                )
            else:
                print_n = DEFAULT_PRINT_N
                print_line = DEFAULT_PRINT_LINE
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

        with st.expander("Condiciones de contorno (BCS)"):
            bc_name = st.text_input("Nombre BC", value="Fixed")
            bc_type = st.selectbox(
                "Tipo BC",
                list(BC_DESCRIPTIONS.keys()),
                format_func=lambda k: f"{k} - {BC_DESCRIPTIONS[k]}",
            )
            st.caption(BC_DESCRIPTIONS[bc_type])
            bc_set = st.selectbox(
                "Conjunto de nodos",
                list(node_sets.keys()),
                disabled=not node_sets,
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
                node_list = node_sets.get(bc_set, [])
                entry = {
                    "name": bc_name,
                    "type": bc_type,
                    "nodes": node_list,
                }
                entry.update(bc_data)
                st.session_state["bcs"].append(entry)

            for bc in st.session_state["bcs"]:
                st.json(bc)

        with st.expander("Interacciones (INTER)"):
            int_type = st.selectbox(
                "Tipo",
                list(INT_DESCRIPTIONS.keys()),
                key="itf_type",
                format_func=lambda k: f"{k} - {INT_DESCRIPTIONS[k]}",
            )
            st.caption(INT_DESCRIPTIONS[int_type])
            int_name = st.text_input("Nombre interfaz", value=f"{int_type}_1")
            slave_set = st.selectbox(
                "Conjunto esclavo",
                list(node_sets.keys()),
                key="slave_set",
                disabled=not node_sets,
            )
            master_set = st.selectbox(
                "Conjunto maestro",
                list(node_sets.keys()),
                key="master_set",
                disabled=not node_sets,
            )
            fric = input_with_help("Fricción", 0.0, "fric")

            gap = stiff = igap = None
            if int_type == "TYPE7":
                gap = input_with_help("Gap", 0.0, "gap")
                stiff = input_with_help("Stiffness", 0.0, "stiff")
                igap = input_with_help("Igap", 0, "igap")

            if st.button("Añadir interfaz") and slave_set and master_set:
                s_list = node_sets.get(slave_set, [])
                m_list = node_sets.get(master_set, [])
                itf = {
                    "type": int_type,
                    "name": int_name,
                    "slave": s_list,
                    "master": m_list,
                    "fric": fric,
                }
                if int_type == "TYPE7":
                    itf.update({
                        "gap": gap,
                        "stiff": stiff,
                        "igap": int(igap),
                    })
                st.session_state["interfaces"].append(itf)
            for itf in st.session_state["interfaces"]:
                st.json(itf)

        with st.expander("Velocidad inicial (IMPVEL)"):
            vel_set = st.selectbox(
                "Conjunto de nodos",
                list(node_sets.keys()),
                key="vel_set",
                disabled=not node_sets,
            )
            vx = input_with_help(f"Vx ({units[1]}/{units[2]})", 0.0, "vx")
            vy = input_with_help(f"Vy ({units[1]}/{units[2]})", 0.0, "vy")
            vz = input_with_help(f"Vz ({units[1]}/{units[2]})", 0.0, "vz")
            if st.button("Asignar velocidad") and vel_set:
                n_list = node_sets.get(vel_set, [])
                st.session_state["init_vel"] = {
                    "nodes": n_list,
                    "vx": vx,
                    "vy": vy,
                    "vz": vz,
                }
            if st.session_state["init_vel"]:
                st.json(st.session_state["init_vel"])

        with st.expander("Carga de gravedad (GRAVITY)"):
            g = input_with_help(
                f"g ({units[1]}/{units[2]}^2)",
                9.81,
                "grav_g",
            )
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
                st.json(st.session_state["gravity"])

        rad_dir = st.text_input(
            "Directorio de salida",
            value=st.session_state.get("work_dir", str(Path.cwd())),
            key="rad_dir",
        )
        rad_name = st.text_input(
            "Nombre de archivo RAD", value="model_0000", key="rad_name"
        )
        overwrite_rad = st.checkbox("Sobrescribir si existe", value=False, key="overwrite_rad")

        if st.button("Generar .rad"):
            out_dir = Path(rad_dir).expanduser()
            out_dir.mkdir(parents=True, exist_ok=True)
            rad_path = out_dir / f"{rad_name}.rad"
            mesh_path = out_dir / "mesh.inc"
            if (rad_path.exists() or mesh_path.exists()) and not overwrite_rad:
                st.error("El archivo ya existe. Elija otro nombre o directorio")
            else:
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

                    runname=runname,
                    t_end=t_end,
                    anim_dt=anim_dt,
                    tfile_dt=tfile_dt,
                    dt_ratio=dt_ratio,
                    print_n=int(print_n),
                    print_line=int(print_line),
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
                    init_velocity=st.session_state.get("init_vel"),
                    gravity=st.session_state.get("gravity"),
                    units=units,

                )
                st.success(f"Ficheros generados en: {rad_path}")
                lines = rad_path.read_text().splitlines()[:20]
                st.code("\n".join(lines))

        clean_dir = st.text_input(
            "Directorio RAD limpio",
            value=st.session_state.get("work_dir", str(Path.cwd())),
            key="clean_dir",
        )
        clean_name = st.text_input(
            "Nombre archivo RAD limpio", value="minimal", key="clean_name"
        )
        overwrite_clean = st.checkbox(
            "Sobrescribir si existe", value=False, key="overwrite_clean"
        )

        if st.button("Generar .rad limpio"):
            out_dir = Path(clean_dir).expanduser()
            out_dir.mkdir(parents=True, exist_ok=True)
            mesh_path = out_dir / "mesh.inc"

            rad_path = out_dir / f"{clean_name}.rad"
            if rad_path.exists() and not overwrite_clean:
                st.error("El archivo RAD ya existe. Cambie el nombre o directorio")

            else:
                write_mesh_inc(nodes, elements, str(mesh_path))
                from cdb2rad.writer_rad import write_minimal_rad

                write_minimal_rad(
                    str(rad_path),
                    mesh_inc=mesh_path.name,
                    units=units,
                )

                st.success("Archivo RAD limpio generado")
                lines = rad_path.read_text().splitlines()[:20]
                st.code("\n".join(lines))

    # Documentation search with dynamic manual selection
    with help_tab:
        st.subheader("Buscar en documentación")
        doc_choice = st.selectbox(

            "Documento",
            ["Reference Guide", "User Guide", "Theory Manual"],

        )
        query = st.text_input("Término de búsqueda")
        if st.button("Buscar", key="search_docs") and query:
            if doc_choice == "Reference Guide":

                source = (
                    REFERENCE_GUIDE
                    if REFERENCE_GUIDE.exists()
                    else REFERENCE_GUIDE_URL
                )
                link = REFERENCE_GUIDE_URL
            else:
                source = (
                    THEORY_MANUAL
                    if THEORY_MANUAL.exists()
                    else THEORY_MANUAL_URL
                )
                link = THEORY_MANUAL_URL
            try:
                results = search_pdf(source, query)
            except ImportError:
                st.error("PyPDF2 no está instalado. Instala la dependencia para habilitar la búsqueda.")
                results = []
            except Exception as e:  # pragma: no cover - network errors
                st.error(f"No se pudo buscar en el PDF: {e}")
                results = []

            if results:
                for r in results:
                    st.write(r)
            elif results == []:
                st.warning("Sin coincidencias")

        else:
            link = (
                REFERENCE_GUIDE_URL if doc_choice == "Reference Guide" else THEORY_MANUAL_URL
            )

        st.markdown(f"[Abrir {doc_choice}]({link})")
else:
    st.info("Sube un archivo .cdb")
