# 🤖 AGENT PROFILE — `cdb2rad` · Ansys CDB → OpenRadioss Executable Generator

## 🤘 Purpose

This repository implements a lightweight **translator between Ansys `.cdb` files and OpenRadioss `.rad` input decks**.

The agent’s task is to help maintain and extend a Python program that takes as input a `.cdb` file exported from Ansys Mechanical or MAPDL, and produces:

1. A **Radioss input mesh file** (`mesh.inp`) containing:
   - `/NODE`, `/SHELL`, `/BRICK` definitions
   - Formatted in **Radioss Block Input Syntax** (not Abaqus)

2. A complete **Radioss starter file** (`model_0000.rad`) containing:
   - `/BEGIN`, `/INCLUDE`, `/PART`, `/PROP`, `/MAT`, `/END`
   - Optional `/INTER`, `/SENSOR`, `/BOUNDARY`, `/LOAD`, etc.

The output `.rad` file is expected to run **directly in OpenRadioss**.

---

## 🧰 Input format

- `.cdb` file generated from Ansys Mechanical using the command:
  ```apdl
  /prep7
  cdwrite,all,'model','cdb'
  *abort
  ```
  It contains two ASCII blocks:

  NBLOCK → node ID + coordinates

  EBLOCK → element ID, type, material ID, connectivity

ᾞa Output formats
1. mesh.inp (Radioss-compatible)
This is not Abaqus .inp — it’s a Radioss-style mesh include file.

Example:
```
/NODE
      1     0.000000     0.000000     0.000000
      2     0.100000     0.000000     0.000000
...
/SHELL
    1001      1      2      3      4
...
```
2. model_0000.rad (Radioss starter)
Includes structural setup and pointers to mesh:
```
/BEGIN
/INCLUDE "mesh.inp"
/PART/1/1/1
/PROP/SHELL/1 0.8 0
/MAT/LAW1/1 210000 0.3 7800
/END
```

## 📁 Code architecture
```
cdb2rad/
├── parser.py         # Reads .cdb → (nodes, elements)
├── writer_inc.py     # Generates mesh.inp from nodes/elements
├── writer_rad.py     # Assembles model_0000.rad (starter)
├── mapping.json      # Maps Ansys ETYPES to Radioss keywords

scripts/
└── run_all.py        # CLI wrapper (--rad, --inc, --all)
```

## 📌 Expected agent behavior
Codex must be able to:
- Parse NBLOCK → dictionary of {node_id: [x, y, z]}
- Parse EBLOCK → list of (eid, etype, [n1, n2, …])
- Auto-map element type to Radioss (e.g., 4-noded → /SHELL, 8-noded → /BRICK)
- Generate a valid mesh.inp file in Radioss block syntax
- Assemble a starter file (model_0000.rad) with structure and references
- Expand logic to support:
  - /INTER/TYPE7 contact
  - /BOUNDARY, /LOAD, /SENSOR, /ENGINE
  - Additional material laws: /MAT/LAW36, /MAT/PLAS_JOHNS, etc.

## 📍 Documentation links
- Radioss Block Syntax Overview: <https://help.altair.com/hwsolvers/rad/topics/solvers/rad/block_format_overview_r.htm>
- Radioss Input Syntax Reference: <https://help.altair.com/hwsolvers/rad/index.htm>
- OpenRadioss GitHub: <https://github.com/OpenRadioss/OpenRadioss>
- Radioss Examples (Starter/Engine): <https://github.com/OpenRadioss/OpenRadioss-examples>
- OpenRadioss User Documentation: <https://openradioss.atlassian.net/wiki/spaces/OPENRADIOSS/pages/4816906/OpenRadioss+User+Documentation>

## ✅ Development style guide
All modules should use pure Python 3.10+, no external dependencies.

Data structures should be simple:
- Nodes: Dict[int, List[float]]
- Elements: List[Tuple[int, int, List[int]]]

Output .rad files must be directly executable in OpenRadioss with:
```bash
openradioss -i model_0000.rad
```
All scripts must be CLI-testable via run_all.py.

## 🤔 Agent expectations
If Codex is asked to:
- Extend writer modules: ensure all new syntax is compliant with Radioss Block.
- Add material/BC/contact support: use valid Radioss keywords from official docs.
- Refactor parser: maintain robustness and backward compatibility with .cdb structure.

This project serves as a bridge between the Ansys modeling world and open-source Radioss simulation. Codex should support the user in maintaining this pipeline and expanding it into a full Radioss preprocessor.

Para evitar errores con GitHub, revisar frecuentemente los "merge conflicts" antes de hacer commit. Si aparece cualquier bloque de conflicto (<<<<< o >>>>>), resolverlo manualmente y verificar que no queden restos en el código.
