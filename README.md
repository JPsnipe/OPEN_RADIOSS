# OPEN_RADIOSS

Pequeña utilidad en Python para convertir un archivo ``.cdb`` exportado desde
Ansys a un *input deck* compatible con OpenRadioss.

## ¿Qué hace el código?

1. Lee bloques ``NBLOCK`` y ``EBLOCK`` de un ``.cdb``.
2. Genera un fichero ``mesh.inp`` con las tarjetas ``/NODE``, ``/SHELL`` y
   ``/BRICK`` según la conectividad de cada elemento.
3. Opcionalmente crea ``model_0000.rad`` que incluye el ``mesh.inp`` y añade los
   bloques básicos ``/BEGIN``, ``/PART``, ``/PROP``, ``/MAT`` y ``/END``.

## Entrada requerida

Archivo ``.cdb`` con los bloques de nodos y elementos. En ``data/model.cdb`` se
incluye un ejemplo mínimo.

## Salida generada

- ``mesh.inp``: definición de nodos y elementos en sintaxis de bloques Radioss.
- ``model_0000.rad`` (opcional): fichero de inicio que referencia ``mesh.inp``.

## Ejemplo de uso

```bash
python scripts/run_all.py data/model.cdb --inc mesh.inp --rad model_0000.rad
```
