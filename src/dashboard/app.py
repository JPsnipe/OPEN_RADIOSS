import tempfile
from pathlib import Path
import sys
import json
import math
from typing import Dict, List, Tuple, Optional, Set

import plotly.graph_objects as go

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
    selected_eids: Optional[Set[int]] = None,
    max_edges: int = MAX_EDGES,
    max_faces: int = MAX_FACES,
) -> str:
    """Return an HTML snippet with a Plotly-based mesh viewer."""

    if selected_eids:
        elements = [e for e in elements if e[0] in selected_eids]

    if not nodes or not elements:
        return "<p>No data</p>"

    def elem_edges(nids: List[int]) -> List[Tuple[int, int]]:
        if len(nids) == 4:
            idx = [(0, 1), (1, 2), (2, 3), (3, 0)]
        elif len(nids) == 3:
            idx = [(0, 1), (1, 2), (2, 0)]
        elif len(nids) in (8, 20):
            idx = [
                (0, 1), (1, 2), (2, 3), (3, 0),
                (4, 5), (5, 6), (6, 7), (7, 4),
                (0, 4), (1, 5), (2, 6), (3, 7),
            ]
        elif len(nids) in (4, 10):
            idx = [
                (0, 1), (1, 2), (2, 0),
                (0, 3), (1, 3), (2, 3),
            ]
        else:
            idx = [(i, (i + 1) % len(nids)) for i in range(len(nids))]
        return [(nids[a], nids[b]) for a, b in idx if a < len(nids) and b < len(nids)]

    def elem_faces(nids: List[int]) -> List[Tuple[int, int, int]]:
        if len(nids) == 4:
            idx = [(0, 1, 2), (0, 2, 3)]
        elif len(nids) == 3:
            idx = [(0, 1, 2)]
        elif len(nids) in (8, 20):
            idx = [
                (0, 1, 2), (0, 2, 3),
                (4, 5, 6), (4, 6, 7),
                (0, 1, 5), (0, 5, 4),
                (1, 2, 6), (1, 6, 5),
                (2, 3, 7), (2, 7, 6),
                (3, 0, 4), (3, 4, 7),
            ]
        elif len(nids) in (4, 10):
            idx = [
                (0, 1, 2),
                (0, 1, 3),
                (1, 2, 3),
                (0, 2, 3),
            ]
        else:
            idx = []
        return [(nids[a], nids[b], nids[c]) for a, b, c in idx]

    edges: List[Tuple[int, int]] = []
    faces: List[Tuple[int, int, int]] = []
    seen: Set[Tuple[int, int]] = set()

    for _eid, _et, nids in elements:
        for a, b in elem_edges(nids):
            key = tuple(sorted((a, b)))
            if key in seen:
                continue
            if a in nodes and b in nodes:
                seen.add(key)
                edges.append((a, b))
            if len(edges) >= max_edges:
                break
        for tri in elem_faces(nids):
            if len(faces) < max_faces:
                faces.append(tri)
        if len(edges) >= max_edges and len(faces) >= max_faces:
            break

    id_to_idx = {nid: i for i, nid in enumerate(nodes)}
    pts = list(nodes.values())

    line_x: List[float] = []
    line_y: List[float] = []
    line_z: List[float] = []
    for a, b in edges:
        pa = nodes[a]; pb = nodes[b]
        line_x += [pa[0], pb[0], None]
        line_y += [pa[1], pb[1], None]
        line_z += [pa[2], pb[2], None]

    fi: List[int] = []
    fj: List[int] = []
    fk: List[int] = []
    for tri in faces:
        if all(n in id_to_idx for n in tri):
            fi.append(id_to_idx[tri[0]])
            fj.append(id_to_idx[tri[1]])
            fk.append(id_to_idx[tri[2]])

    fig = go.Figure()
    if line_x:
        fig.add_trace(
            go.Scatter3d(
                x=line_x,
                y=line_y,
                z=line_z,
                mode="lines",
                line=dict(color="blue", width=2),
                showlegend=False,
            )
        )
    if fi:
        fig.add_trace(
            go.Mesh3d(
                x=[p[0] for p in pts],
                y=[p[1] for p in pts],
                z=[p[2] for p in pts],
                i=fi,
                j=fj,
                k=fk,
                color="lightgray",
                opacity=0.5,
                flatshading=True,
                showscale=False,
            )
        )

    fig.update_layout(
        scene_aspectmode="data",
        margin=dict(l=0, r=0, t=0, b=0),
        width=400,
        height=400,
    )

    return fig.to_html(include_plotlyjs="cdn")


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

        if "impact_materials" not in st.session_state:
            st.session_state["impact_materials"] = []
        if "bcs" not in st.session_state:
            st.session_state["bcs"] = []
        if "interfaces" not in st.session_state:
            st.session_state["interfaces"] = []
        if "init_vel" not in st.session_state:
            st.session_state["init_vel"] = None

        with st.expander("Definición de materiales"):
            thickness = st.number_input("Grosor", value=1.0, min_value=0.0)
            young = st.number_input("Módulo E", value=210000.0)
            poisson = st.number_input("Coeficiente de Poisson", value=0.3)
            density = st.number_input("Densidad", value=7800.0)

            use_cdb_mats = st.checkbox("Incluir materiales del CDB", value=False)
            use_impact = st.checkbox("Incluir materiales de impacto", value=True)

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


        with st.expander("Control del cálculo"):
            runname = st.text_input("Nombre de la simulación", value="model")
            t_end = st.number_input("Tiempo final", value=0.01, format="%.5f")
            anim_dt = st.number_input("Paso animación", value=0.001, format="%.5f")
            tfile_dt = st.number_input("Intervalo historial", value=0.00001, format="%.5f")
            dt_ratio = st.number_input(
                "Factor seguridad DT", value=0.9, min_value=0.0, max_value=1.0
            )

        with st.expander("Condiciones de contorno (BCS)"):
            bc_name = st.text_input("Nombre BC", value="Fixed")
            bc_tra = st.text_input("Traslación (111/000)", value="111")
            bc_rot = st.text_input("Rotación (111/000)", value="111")
            bc_set = st.selectbox(
                "Conjunto de nodos",
                list(node_sets.keys()),
                disabled=not node_sets,
            )
            if st.button("Añadir BC") and bc_set:
                node_list = node_sets.get(bc_set, [])
                st.session_state["bcs"].append(
                    {
                        "name": bc_name,
                        "tra": bc_tra,
                        "rot": bc_rot,
                        "nodes": node_list,
                    }
                )
            for bc in st.session_state["bcs"]:
                st.json(bc)

        with st.expander("Interacciones (INTER)"):
            int_name = st.text_input("Nombre interfaz", value="Tie")
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
            fric = st.number_input("Fricción", value=0.0)
            if st.button("Añadir interfaz") and slave_set and master_set:
                s_list = node_sets.get(slave_set, [])
                m_list = node_sets.get(master_set, [])
                st.session_state["interfaces"].append(
                    {
                        "name": int_name,
                        "slave": s_list,
                        "master": m_list,
                        "fric": fric,
                    }
                )
            for itf in st.session_state["interfaces"]:
                st.json(itf)

        with st.expander("Velocidad inicial (IMPVEL)"):
            vel_set = st.selectbox(
                "Conjunto de nodos",
                list(node_sets.keys()),
                key="vel_set",
                disabled=not node_sets,
            )
            vx = st.number_input("Vx", value=0.0)
            vy = st.number_input("Vy", value=0.0)
            vz = st.number_input("Vz", value=0.0)
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

                write_minimal_rad(str(rad_path), mesh_inc=mesh_path.name)

                st.success("Archivo RAD limpio generado")
                lines = rad_path.read_text().splitlines()[:20]
                st.code("\n".join(lines))
else:
    st.info("Sube un archivo .cdb")
