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

## Instalación de dependencias

Instala las librerías necesarias (``streamlit``, ``meshio``, ``vtk`` y
``wslink``) con ``pip`` antes de ejecutar cualquier script:

```bash
pip install -r requirements.txt
```

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

Las condiciones de contorno incluyen ahora la opción de **movimiento
prescrito** (`/BOUNDARY/PRESCRIBED_MOTION`) además de las fijaciones
tradicionales (`/BCS`). Estas se pueden seleccionar desde el dashboard y se
exportan con la sintaxis correspondiente del Reference Guide.

## Materiales por defecto

Cuando no se proporcionan propiedades específicas, el generador aplica
parámetros típicos de aceros de automoción para todas las leyes de material
soportadas (LAW1, LAW2, LAW27, LAW36 y LAW44). Estos valores incluyen
``E=210000`` MPa, ``nu=0.3`` y ``rho=7800`` kg/m\ :sup:`3`, además de
constantes habituales para cada ley (por ejemplo, ``A=220`` y ``B=450`` en
Johnson--Cook).

Cada bloque está descrito en detalle en la guía oficial de comandos de
Radioss. Para depurar y ampliar estos ficheros se recomienda consultar el
[Altair Radioss 2022 Reference Guide](https://2022.help.altair.com/2022/simulation/pdfs/radopen/AltairRadioss_2022_ReferenceGuide.pdf) es la referencia principal para la sintaxis y
[Overview of the Input Reference Guide](https://help.altair.com/hwsolvers/rad/topics/solvers/rad/overview_ref_guide_rad_c.htm).
En ella se explica el formato, las palabras clave disponibles y la estructura
del ``starter`` y los ficheros ``engine``.

## Criterios de fallo

El dashboard permite añadir tarjetas ``/FAIL`` para distintos modelos.
Para el criterio de daño **Johnson-Cook** se suelen emplear los siguientes
coeficientes de referencia:

```text
D1 = -0.77
D2 = 1.45
D3 = -0.47
D4 = 0.0
D5 = 1.6
```

Si en el material solo se indica ``"FAIL": {"TYPE": "JOHNSON"}``, estos valores
se completarán automáticamente.

## Ejemplo de uso

```bash
python scripts/run_all.py data_files/model.cdb --inc mesh.inc --rad model_0000.rad
```

Por defecto, ``model_0000.rad`` incluye la línea ``#include mesh.inc``. Con la
opción ``--skip-include`` se genera el ``.rad`` sin esa referencia:

```bash
python scripts/run_all.py data_files/model.cdb --rad model.rad --skip-include
```

Para generar un ``.rad`` limpio sin tarjetas de control ni material por defecto
pueden emplearse las opciones ``--no-run-cards`` y ``--no-default-material``:

```bash
python scripts/run_all.py data_files/model.cdb --rad vacio.rad --no-run-cards --no-default-material
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

Se puede subir un archivo ``.cdb`` propio. La interfaz cuenta con varias
pestañas principales:

- En la parte superior se puede elegir el **sistema de unidades** (``SI`` o
  ``Imperial``). Las casillas de entrada mostrarán automáticamente la unidad
  correspondiente en cada parámetro.

- **Información** resumen de nodos y elementos.
- **Vista 3D** previsualización ligera de la malla con opción de seleccionar
  los *name selections* que se quieran mostrar. Desde esta pestaña también es
  posible **exportar VTK** indicando directorio y formato. Por defecto se sugiere
  `C:\JAVIER\OPEN_RADIOSS\paraview\data` como directorio de salida.
- **Propiedades** permite definir propiedades y partes que luego se incluirán en
  el ``starter``.
- **Generar INC** permite crear ``mesh.inc`` y muestra sus primeras líneas. \


- **Generar INC** permite crear ``mesh.inc`` y muestra sus primeras líneas. \

  Incluye casillas para decidir si exportar las selecciones nombradas y los
  materiales.

- **Generar RAD** para introducir parámetros de cálculo, definir **Propiedades** y obtener
  ``model_0000.rad``.
Dentro de esta pestaña se incluye un bloque **Propiedades** donde se pueden crear tarjetas `/PROP` y asignarlas a `/PART` mediante el ID de material. Las tablas de propiedades y partes se muestran antes de generar el archivo.
Se incluyen casillas opcionales para **sobrescribir** los archivos
``.inc`` o ``.rad`` si ya existen en el directorio de salida.
- La opción **Incluir materiales del CDB** está desactivada por defecto;
  actívala si deseas copiar al starter los materiales extraídos del `.cdb`.


La pestaña *Generar RAD* también permite definir condiciones de contorno

(tarjetas ``/BCS``), contactos simples (``/INTER/TYPE2``) o generales
(``/INTER/TYPE7``), velocidades iniciales (``/IMPVEL``) y cargas de
gravedad (``/GRAVITY``) seleccionando las *name selections* de nodos en un
desplegable. Estos campos se pueden editar, añadir o eliminar en el panel
correspondiente antes de generar el archivo.
El panel de gravedad está junto a **Velocidad inicial** y permite indicar la magnitud `g` y la dirección `(nx, ny, nz)`.


Tras pulsar *Generar .inc* o *Generar .rad* se muestran las primeras líneas de
los ficheros generados.
Cada pestaña permite elegir el directorio de salida y el nombre (sin extensión)
del archivo para guardar fácilmente los resultados.

### Ayuda interactiva

La pestaña **Ayuda** ofrece enlaces directos a la documentación principal de Radioss: la [Reference Guide](https://2022.help.altair.com/2022/simulation/pdfs/radopen/AltairRadioss_2022_ReferenceGuide.pdf), la [User Guide](https://2022.help.altair.com/2022/simulation/pdfs/radopen/AltairRadioss_2022_UserGuide.pdf) y el [Theory Manual](https://2022.help.altair.com/2022/simulation/pdfs/radopen/AltairRadioss_2022_TheoryManual.pdf). Puedes descargar estos PDF con ``scripts/download_docs.py`` para consultarlos sin conexión.

### Vista 3D con ParaView Web

Para una visualización más completa de la malla se puede utilizar un servidor

**ParaView Web**. El script ``scripts/pv_visualizer.py`` convierte
cualquier malla soportada a ``.vtk`` o ``.vtp`` de forma temporal y lanza un
servidor wslink (host 127.0.0.1 y puerto 8080 por defecto). Ahora también es
posible generar el fichero VTK en memoria desde la propia aplicación:


Además, desde la pestaña *Vista 3D* se puede guardar el archivo con el botón
**Generar VTK**, especificando la ruta y el nombre deseado.


```bash
python scripts/pv_visualizer.py --data data_files/model.cdb --port 8080 --verbose

```

Al ejecutar el comando se mostrará la URL del visualizador. Desde la pestaña
**Vista 3D** del dashboard se puede iniciar el servidor y el visor quedará
embebido directamente en la aplicación usando ``static/vtk_viewer.html`` para
conectarse vía WebSocket y visualizar la malla con todas las herramientas de
ParaView. La función ``launch_paraview_server`` acepta ahora ``nodes`` y
``elements`` para exportar el VTK de forma dinámica. Si se desea convertir un
archivo sin lanzar el servidor puede
utilizarse ``scripts/convert_to_vtk.py``:

```bash
python scripts/convert_to_vtk.py model.cdb mesh.vtk
```


