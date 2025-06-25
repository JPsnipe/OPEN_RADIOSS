# OPEN_RADIOSS

Pequeña utilidad en Python para convertir un archivo ``.cdb`` exportado desde
Ansys a un *input deck* compatible con OpenRadioss.

## ¿Qué hace el código?

1. Lee bloques ``NBLOCK`` y ``EBLOCK`` de un ``.cdb``.
2. Detecta selecciones nombradas (``CMBLOCK``) y datos de material
   (``MPDATA``).
3. Genera un fichero ``mesh.inc`` con ``/NODE`` y bloques de elementos
   derivados de ``mapping.json`` (``/SHELL``, ``/BRICK``, ``/TETRA``...). Las
   selecciones y los materiales se exportan en formato Radioss.
4. Crea ``model_0000.rad`` que referencia ``mesh.inc`` mediante ``#include`` y define propiedades,
   materiales, condiciones de contorno y ejemplos de contacto y carga.

## Entrada requerida

Archivo ``.cdb`` con los bloques de nodos y elementos. En ``data_files/model.cdb`` se incluye un ejemplo mínimo. Este mismo fichero se emplea en las pruebas
unitarias (ver ``tests/test_basic.py``) y sirve de punto de partida para los
ejemplos de la documentación.

## Salida generada

 - ``mesh.inc``: definición de nodos y elementos.
- ``model_0000.rad``: fichero de inicio con propiedades, material y BCs.
 - ``minimal.rad``: starter simplificado solo con ``#include mesh.inc``.

## Configuración del ``.rad``

El *starter* ``model_0000.rad`` sigue la sintaxis por bloques de Radioss. Un
fichero mínimo contiene:

```text
/BEGIN
/INCLUDE "mesh.inc"
/PART
...   # definición de propiedades y materiales
/END
```

El ``starter`` se organiza siguiendo un orden similar al de los ejemplos de
OpenRadioss. Primero se colocan las tarjetas de control (``/RUN`` y
parámetros de tiempo), seguidas de los materiales. A continuación se
incluyen los nodos mediante ``#include`` y se definen las condiciones de
contorno. Finalmente se añaden partes y propiedades antes de otras
tarjetas opcionales como contactos o cargas iniciales.

Cada bloque está descrito en detalle en la guía oficial de comandos de
Radioss. Para depurar y ampliar estos ficheros se recomienda consultar el
[Altair Radioss 2022 Reference Guide](https://2022.help.altair.com/2022/simulation/pdfs/radopen/AltairRadioss_2022_ReferenceGuide.pdf) es la referencia principal para la sintaxis y
[Overview of the Input Reference Guide](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/overview_ref_guide_rad_c.htm).
En ella se explica el formato, las palabras clave disponibles y la estructura
del ``starter`` y los ficheros ``engine``.

## Ejemplo de uso

```bash
python scripts/run_all.py data_files/model.cdb --inc mesh.inc --rad model_0000.rad
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
    --exec openradioss_bin/OpenRadioss/exec/starter_linux64_gf
```

Antes de ejecutar es necesario definir dos variables de entorno para que los
binarios de OpenRadioss encuentren las bibliotecas y ficheros de configuración:

```bash
export LD_LIBRARY_PATH=$PWD/openradioss_bin/OpenRadioss/extlib/hm_reader/linux64
export RAD_CFG_PATH=$PWD/openradioss_bin/OpenRadioss/hm_cfg_files
```

Con estas variables se puede lanzar el *starter* directamente:

```bash
openradioss_bin/OpenRadioss/exec/starter_linux64_gf -i model.rad
```

Para lanzar las pruebas:

```bash
pytest -q
```

### Entorno automático

Para recrear el entorno de pruebas siguiendo las instrucciones de
[HOWTO](https://github.com/OpenRadioss/OpenRadioss/blob/main/HOWTO.md) se ha
añadido el script ``scripts/setup_test_env.py``. Ejecuta la creación del
``virtualenv`` y descarga la última versión de OpenRadioss:

```bash
python scripts/setup_test_env.py
```

Al terminar, se muestran las variables de entorno necesarias para ejecutar el
``starter`` y se pueden lanzar las pruebas con ``pytest -q``.

## Interfaz web

Se incluye una pequeña interfaz en Streamlit para cargar un `.cdb`, visualizar
el número y tipo de elementos y generar los ficheros ``mesh.inc`` y
``model_0000.rad`` de forma interactiva. Para ejecutarla:

```bash
streamlit run src/dashboard/app.py
```

Se puede subir un archivo ``.cdb`` propio. La interfaz cuenta con cuatro
pestañas principales:

- **Información** resumen de nodos y elementos.
- **Vista 3D** previsualización ligera de la malla con opción de seleccionar
  los *name selections* que se quieran mostrar.

-- **Generar INC** permite crear ``mesh.inc`` y muestra sus primeras líneas. \
  Incluye casillas para decidir si exportar las selecciones nombradas y los
  materiales.

- **Generar RAD** para introducir parámetros de cálculo y obtener
  ``model_0000.rad``.
Se incluyen casillas opcionales para **sobrescribir** los archivos
``.inc`` o ``.rad`` si ya existen en el directorio de salida.
- La opción **Incluir materiales del CDB** está desactivada por defecto;
  actívala si deseas copiar al starter los materiales extraídos del `.cdb`.

- **RAD limpio (.rad)** genera ``minimal.rad`` para probar rápidamente ``mesh.inc``.

La pestaña *Generar RAD* también permite definir condiciones de contorno
(tarjetas ``/BCS``), contactos simples (``/INTER/TYPE2``) o generales
(``/INTER/TYPE7``), velocidades iniciales (``/IMPVEL``) y cargas de
gravedad (``/GRAVITY``) seleccionando las *name selections* de nodos en un
desplegable. Estos campos se pueden editar y añadir en el panel correspondiente
antes de generar el archivo.

Tras pulsar *Generar .inc* o *Generar .rad* se muestran las primeras líneas de
los ficheros generados.
Cada pestaña permite elegir el directorio de salida y el nombre (sin extensión)
del archivo para guardar fácilmente los resultados.
