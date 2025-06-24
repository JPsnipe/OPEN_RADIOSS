# OPEN_RADIOSS

Pequeña utilidad en Python para convertir un archivo ``.cdb`` exportado desde
Ansys a un *input deck* compatible con OpenRadioss.

## ¿Qué hace el código?

1. Lee bloques ``NBLOCK`` y ``EBLOCK`` de un ``.cdb``.
2. Genera un fichero ``mesh.inp`` con ``/NODE`` y bloques de elementos
   derivados de ``mapping.json`` (``/SHELL``, ``/BRICK``, ``/TETRA``...).
3. Crea ``model_0000.rad`` que incluye ``mesh.inp`` y define propiedades,
   materiales, condiciones de contorno y ejemplos de contacto y carga.

## Entrada requerida

Archivo ``.cdb`` con los bloques de nodos y elementos. En ``data/model.cdb`` se
incluye un ejemplo mínimo.

## Salida generada

 - ``mesh.inp``: definición de nodos y elementos.
 - ``model_0000.rad``: fichero de inicio con propiedades, material y BCs.

## Ejemplo de uso

```bash
python scripts/run_all.py data/model.cdb --inc mesh.inp --rad model_0000.rad
```

Para lanzar las pruebas:

```bash
pytest -q
```
