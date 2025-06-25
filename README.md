# OPEN_RADIOSS

Pequeña utilidad en Python para convertir un archivo ``.cdb`` exportado desde
Ansys a un *input deck* compatible con OpenRadioss.

## ¿Qué hace el código?

1. Lee bloques ``NBLOCK`` y ``EBLOCK`` de un ``.cdb``.
2. Detecta selecciones nombradas (``CMBLOCK``) y datos de material
   (``MPDATA``).
3. Genera un fichero ``mesh.inp`` con ``/NODE`` y bloques de elementos
   derivados de ``mapping.json`` (``/SHELL``, ``/BRICK``, ``/TETRA``...). Las
   selecciones, los materiales y el espesor de ``/PROP/SHELL`` se exportan en
   formato Radioss.
4. Crea ``model_0000.rad`` que incluye ``mesh.inp`` y define propiedades
   (usando el espesor hallado en ``SECBLOCK``), materiales, condiciones de
   contorno y ejemplos de contacto y carga.

## Entrada requerida

Archivo ``.cdb`` con los bloques de nodos y elementos. En ``data_files/model.cdb`` se incluye un ejemplo mínimo. Este mismo fichero se emplea en las pruebas
unitarias (ver ``tests/test_basic.py``) y sirve de punto de partida para los
ejemplos de la documentación.

## Salida generada

 - ``mesh.inp``: definición de nodos y elementos.
 - ``model_0000.rad``: fichero de inicio con propiedades, material y BCs.

## Ejemplo de uso

```bash
python scripts/run_all.py data_files/model.cdb --inc mesh.inp --rad model_0000.rad
```

### Entorno virtual y OpenRadioss

Para crear un entorno virtual con `pytest` y descargar la última
versión binaria de OpenRadioss:

```bash
python scripts/create_venv.py
python scripts/download_openradioss.py
```

Después se puede ejecutar OpenRadioss sobre el fichero generado:

```bash
python scripts/run_all.py data_files/model.cdb --rad model.rad \
    --exec openradioss_bin/exec/starter_linux64_gf
```

Para lanzar las pruebas:

```bash
pytest -q
```

## Interfaz web

Se incluye una pequeña interfaz en Streamlit para cargar un `.cdb`, visualizar
el número y tipo de elementos, los materiales y el espesor detectado para las
"shell" y generar los ficheros ``mesh.inp`` y ``model_0000.rad`` de forma
interactiva. Para ejecutarla:

```bash
streamlit run src/dashboard/app.py
```

Sube un archivo ``.cdb`` y pulsa *Generar input deck* para ver las primeras
líneas de ``mesh.inp`` junto con un resumen de tipos de elemento y los
materiales trasladados.
