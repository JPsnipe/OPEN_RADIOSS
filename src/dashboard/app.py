import tempfile
from pathlib import Path

import streamlit as st

from cdb2rad.parser import parse_cdb
from cdb2rad.writer_rad import write_rad


@st.cache_data(ttl=3600)
def load_cdb(path: str):
    return parse_cdb(path)


st.title("CDB → OpenRadioss")

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
    st.write("Nodos:", len(nodes))
    st.write("Elementos:", len(elements))
    st.write("Conjuntos de nodos:", len(node_sets))
    st.write("Conjuntos de elementos:", len(elem_sets))
    st.write("Materiales:", len(materials))

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
else:
    st.info("Sube o selecciona un archivo .cdb")
