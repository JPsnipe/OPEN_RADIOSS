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
5. Los grupos de elementos asignados a una parte generan de forma automática
   una entrada ``/SUBSET`` para que ``subset_ID`` de ``/PART`` apunte al grupo
   seleccionado. Si el nombre del grupo es numérico, su valor se mantiene como
   ID; los demás se numeran de forma secuencial empezando tras el mayor ID
   existente. Definir subsets manualmente es opcional, ya que en el menú
   desplegable aparecen todos los grupos leídos del ``.cdb`` junto con los
   subsets previamente guardados. Las previsualizaciones del dashboard y los
   scripts ``write_starter`` y ``write_rad`` muestran exactamente el mismo ID
   que se escribirá en ``.rad``.


## Entrada requerida

Archivo ``.cdb`` con los bloques de nodos y elementos. En ``data_files/model.cdb`` se incluye un ejemplo mínimo. Este mismo fichero se emplea en las pruebas
unitarias (ver ``tests/test_basic.py``) y sirve de punto de partida para los
ejemplos de la documentación.

## Salida generada

- ``mesh.inc``: definición de nodos y elementos.
- ``model_0000.rad``: fichero de inicio con propiedades, material y BCs.
## ⚠️ Orden obligatoria

Todos los campos enteros de cada tarjeta deben escribirse con sus lineas completas y parametros obligatorios. Consulta siempre la [documentacion de Radioss 2022](https://help.altair.com/hwsolvers/rad/index.htm) para verificar la sintaxis.


### Tipos de elemento admitidos

El archivo ``cdb2rad/mapping.json`` define la correspondencia básica entre
los ``ETYP`` de Ansys y las palabras clave de Radioss utilizadas en
``mesh.inc``. Los valores incluidos por defecto son:

| ETYP | Nombre Ansys  | Radioss |
|-----:|---------------|---------|
| 1    | SOLID185      | /BRICK  |
| 2    | SHELL181      | /SHELL  |
| 4    | SHELL63       | /SHELL  |
| 45   | SHELL45       | /SHELL  |
| 181  | SHELL181      | /SHELL  |
| 182  | SHELL281      | /SHELL  |
| 185  | SOLID185      | /BRICK  |
| 186  | SOLID186      | /BRICK  |
| 187  | SOLID187      | /TETRA  |

Si se encuentra un ``ETYP`` no contemplado en la tabla, el número de nodos
del elemento se utiliza para decidir entre ``/SHELL``, ``/BRICK`` o ``/TETRA``.


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

## Ejemplo de uso

```bash
python scripts/run_all.py data_files/model.cdb --inc mesh.inc --starter model_0000.rad
```

El parámetro `--rad` sigue funcionando como alias de `--starter`, pero está
deprecado y se mantiene solo para compatibilidad.

Por defecto, ``model_0000.rad`` incluye la línea ``#include mesh.inc``. Con la
opción ``--skip-include`` se genera el ``.rad`` sin esa referencia:

```bash
python scripts/run_all.py data_files/model.cdb --starter model.rad --skip-include
```

Si se desea ignorar completamente los materiales leídos del ``.cdb`` basta con
añadir ``--no-cdb-materials``:

```bash
python scripts/run_all.py data_files/model.cdb --starter sin_mats.rad --no-cdb-materials --no-default-material
```

Si se omite ``--no-default-material`` y existen tarjetas ``/PART``, el script
añade de forma automática un material genérico ``/MAT/LAW1`` para evitar
errores por IDs no definidos.

Para generar un ``.rad`` limpio sin tarjetas de control ni material por defecto
pueden emplearse las opciones ``--no-run-cards`` y ``--no-default-material``:

```bash
python scripts/run_all.py data_files/model.cdb --starter vacio.rad --no-run-cards --no-default-material
```

La opción `--all` permite generar automáticamente los tres ficheros básicos
(``mesh.inc``, ``model_0000.rad`` y ``model_0001.rad``) si no se indican rutas
de salida:

```bash
python scripts/run_all.py data_files/model.cdb --all
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
python scripts/run_all.py data_files/model.cdb --starter model.rad \
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

### Ejecutar desde el dashboard

Tras subir un `.cdb` en la UI, aparece una pestaña "Ejecutar":

- Configura `starter_linux64_gf` y `engine_linux64_gf` (se autocompletan si usaste `download_openradioss.py`).
- Define `LD_LIBRARY_PATH` y `RAD_CFG_PATH` (también se autocompletan).
- Usa “Generar y ejecutar Starter” para crear `mesh.inc`, `model_0000.rad` y `model_0001.rad` con el estado actual y lanzar el starter.
- Consulta `stdout/stderr` y refresca el `*.out` con “Refrescar salida”.
- Opcional: “Descargar ejemplo desde URL” permite pegar enlaces a `.rad` de la documentación oficial y ejecutarlos sin traducir desde `.cdb`.

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
- **Generar INC** permite crear ``mesh.inc`` y muestra sus primeras líneas.
  Incluye casillas para decidir si exportar las selecciones nombradas y los
  materiales. La tabla **Grupos importados** indica el tipo de elemento en
  Radioss y el nombre Ansys asociado a cada conjunto.

- **Generar RAD** para introducir parámetros de cálculo, definir **Propiedades** y obtener
  ``model_0000.rad``.

- **Editor RAD** permite revisar los ficheros generados y editarlos manualmente.
  Con el campo *Guardar como* y el botón **Exportar copia** se puede crear una
  copia con otro nombre en el mismo directorio de salida.
Dentro de esta pestaña se incluye un bloque **Propiedades** donde se pueden crear tarjetas `/PROP` y asignarlas a `/PART` mediante el ID de material. Las tablas de propiedades y partes se muestran antes de generar el archivo. Además, existen botones rápidos para generar propiedades **Hexa8**, **Tetra4** y **Quad4** con parámetros recomendados por la ayuda de Radioss.
Se incluyen casillas opcionales para **sobrescribir** los archivos
``.inc`` o ``.rad`` si ya existen en el directorio de salida.
- La opción **Incluir materiales del CDB** está desactivada por defecto;
  actívala si deseas copiar al starter los materiales extraídos del `.cdb`.
  Si permanece desactivada y no se definen materiales de impacto,
  el archivo resultante no contendrá tarjetas `/MAT`.
- Si aparece el mensaje de error "Material ID no definido..." al generar el
  ``starter``, activa esta opción o define el material manualmente en la sección
  de **impacto**.


La pestaña *Generar RAD* también permite definir condiciones de contorno

(tarjetas ``/BCS``), contactos simples (``/INTER/TYPE2``) o generales
(``/INTER/TYPE7``), velocidades iniciales (``/IMPVEL``) y cargas de
gravedad (``/GRAV``) seleccionando las *name selections* de nodos en un
desplegable. Estos campos se pueden editar, añadir o eliminar en el panel
correspondiente antes de generar el archivo.
Para contactos ``TYPE7`` se puede especificar ``fric_ID`` para enlazar una
tarjeta ``/FRICTION`` separada:

```python
inter = [{
    'type': 'TYPE7',
    'slave': [1, 2],
    'master': [3, 4],
    'fric_ID': 10,
    'friction': {'Ifric': 1, 'C1': 0.3},
}]
```
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
Los conjuntos leídos del ``.cdb`` se exportan como arrays de nodos y elementos
en los ficheros ``.vtk`` o ``.vtp`` para poder filtrarlos en ParaView.


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

