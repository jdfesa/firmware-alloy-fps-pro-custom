# Publicación: criterios y registro de revisión

Revisión editorial: **2026-10-31**. Esta guía distingue los criterios vigentes
del registro histórico de publicación. El repositorio ya tiene historial,
remoto público y [LICENSE (GNU GPL versión 2)](../LICENSE); las referencias a
«sin commits», «sin remoto» o «licencia pendiente» describen fases anteriores.

## Criterios antes de cada commit y push

1. Revisar la lista **real** de archivos staged y su diff. No publicar la carpeta
   completa como ZIP ni forzar archivos ignorados.
2. Revisar también el historial que vaya a enviarse. Una revisión del árbol de
   trabajo no audita automáticamente los commits anteriores.
3. No confiar en `.gitignore` para retirar archivos ya versionados o sus copias
   del historial. [Documentación de GitHub](https://docs.github.com/en/get-started/git-basics/ignoring-files).
4. Revisar nombre y correo del commit antes de publicar. No incluir credenciales,
   direcciones privadas, rutas personales ni identificadores de etiqueta.
5. Conservar encabezados SPDX y revisar atribuciones/licencias de terceros.
   La presencia de LICENSE no certifica permiso para redistribuir el updater,
   la DLL o la imagen propietaria analizados: permanecen excluidos.
6. Mantener visibles el carácter experimental, el alcance de una unidad y la
   ausencia de backup/restauración OEM. No publicar una release como estable.
7. Escribir documentación autónoma, centrada en el HyperX: requisitos por tarea,
   resultados, límites y procedimientos. No incluir pertenencias, instrucciones
   del chat o autorizaciones personales como si fueran requisitos generales.
8. Usar Conventional Commits en inglés. Un commit no implica autorización de
   push; revisar el destino y publicar solo cuando se solicite explícitamente.

```sh
rtk git status --short
rtk git diff --cached --stat
rtk git diff --cached
rtk git ls-files
```

Repetir la revisión al añadir capturas, logs, paquetes, configuraciones o nuevos
metadatos. Ninguna exclusión evita que `git add -f` la fuerce. La revisión de
atribuciones de terceros y la preparación reproducible desde un clon limpio
siguen pendientes; no se certifican por esta revisión editorial.

## Qué se permite y qué se excluye

**Material público:** fuentes propias del port y scripts, pruebas, documentación,
matriz inferida, evidencia saneada, estado de validación y locks de herramientas.
En `artifacts/analysis` solo están permitidos cuatro metadatos revisados:

- `arm-build-custom42.json`
- `arm-build-default.json`
- `extraction.json`
- `vendor-provenance.json`

**Excluidos por defecto:** herramientas y dependencias descargadas, firmware
propietario, updater/DLL, builds, desensamblado propietario, exportaciones REA
sin sanear, logs crudos, informes de tamaños/símbolos, fotos, temporales del
editor, configuraciones locales y snapshots privados de mapas. Las reglas
cubren varios formatos comunes de credenciales, no todo secreto posible.

La excepción exacta para `docs/images/vial-tkl-full.png` no autoriza otras fotos
ni capturas. No ampliar la lista de excepciones sin revisar el contenido real.
SKU, VID/PID, modelo, familia MCU y hashes de artefactos son datos técnicos;
números de serie, SP y códigos individuales de la etiqueta no se publican.

## Alcance de las revisiones técnicas

La revisión inicial de 2026-10-29 examinó candidatos con patrones de credenciales,
correos, rutas personales, direcciones privadas e identificadores de etiqueta.
No detectó coincidencias en esa selección. Git aislado comprobó 11 casos de
exclusión. Es una revisión acotada, **no una garantía de ausencia de todo secreto**
ni una auditoría automática de todo el historial.

Las ampliaciones revisaron fuentes C/ASM/Python, JSON generados, referencias de
protocolo y tests. No se incorporaron dependencias descargadas, updater/DLL,
binarios instalables o credenciales. Los espacios de contexto de un `.patch`
son parte del formato y no se recortan. En pruebas sin material propietario o
toolchain se informan las omisiones explícitas, no se declaran pruebas inexistentes.

La marca `vial:f64c2b3c` es pública y el UID experimental identifica el diseño,
no una unidad individual. No confundir estos datos con seriales privados.

### Captura GUI permitida

`docs/images/vial-tkl-full.png` muestra solo la ventana Vial. La revisión no
halló escritorio ajeno, cuentas, rutas, seriales o contenido personal; tampoco
chunks PNG de texto o rutas privadas. EXIF contenía anchura/altura y había perfil
de color. No se retocaron píxeles para simular teclas funcionales. Las cinco
casillas `KC_NO` permanecen vacías y el pie lo explica. El reemplazo con más zoom
usó el mismo archivo permitido. La captura de un error de comunicación quedó
fuera del versionado.

### Procedencia del candidato ensayado

`toolchains/reconstruction-record.json` conserva revisiones, hashes, propiedades
de la app y rutas relativas de fuentes. Cada fuente se contrastó con el commit
indicado. No contiene dumps, credenciales o autorización de flash ni garantiza
reproducción limpia byte a byte. La revisión editorial de 2026-10-31 no modifica
ese registro ni los indicadores de validación para aparentar una compilación
o prueba de hardware nueva. GitHub conserva fuentes, no restaura el OEM.
