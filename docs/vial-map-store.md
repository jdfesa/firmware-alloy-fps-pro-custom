# Mapa editable con RAM acotada: experimento sin escritura física

> [!NOTE]
> Informe de una fase anterior, conservado por su evidencia y fuentes. No usar
> sus estados provisionales como estado actual ni sus comandos como receta universal.
> Leer primero [README](../README.md), [estado](status-and-limits.md) y
> [seguridad/recuperación](safety-and-recovery.md).

**2026-10-29. Código C probado en host y objeto Cortex-M0 compilado.**
No se enlaza en `vial_readonly`, no implementa un controlador flash ni habilita
SET_KEYCODE en el teclado. El firmware disponible sigue siendo de solo lectura.

## Qué resuelve

`firmware/experiments/vial_store/map_store.c/.h` guarda un mapa de cuatro capas
14×8 en dos bancos **virtuales**. Lee desde el banco válido o desde el mapa
compilado; no duplica los **896 B** del mapa en RAM. El estado del llamador ocupa
**8 B**, además de las variables en pila y lo que requiera un futuro backend.

Cada edición de hasta28 B (orden VIA: keycodes big-endian) construye una nueva
instantánea palabra a palabra en el banco inactivo. Soporta offsets impares,
valida todos los keycodes antes de borrar y evita escribir si nada cambia.
La política de keycodes/posiciones se inyecta: el harness prueba el mapa real
`custom42_fn`, las54 posiciones habilitadas y el rechazo de las cinco averiadas.
Esa política de prueba **no es una traducción completa SonixQMK↔Vial**.

## Formato v1, no mapa de direcciones del MCU

Se simulan dos bancos de1024 B, lectura/programación de palabras LE de4 B,
borrado independiente de cada banco y programación solo1→0. **No se afirma
que ésta sea la geometría del SN32F26x.** Los offsets son relativos al medio
simulado; no se asignó ninguna región física del teclado ni se modificó el linker.

| Offset dentro del banco | Campo |
| --- | --- |
| 0..3 | Magic `AVM1` |
| 4..7 | Esquema `0x01040e08`: formato1,4 capas,14 filas,8 columnas |
| 8..11 | Generación uint32 LE |
| 12..15 | CRC-32/ISO-HDLC de bytes0..11 y32..927 |
| 16..27 | Reservado; debe permanecer `ff` |
| 28..31 | Marca `CMIT`, escrita al final |
| 32..927 | Mapa896 B, keycodes big-endian |
| 928..1023 | Sin uso |

Un cambio incompatible de matriz, semántica, política o formato exige revisar
y cambiar el esquema; no migrar silenciosamente por tener las mismas dimensiones.
El CRC detecta daños accidentales con sus límites habituales: **no autentica
datos ni garantiza detectar todas las corrupciones posibles**.

## Transacción y recuperación simulada

1. Comprobar integridad del banco activo y validar toda la edición propuesta.
2. Borrar solo el banco inactivo y verificar que quedó completamente en `ff`.
3. Escribir cabecera, mapa por palabras y CRC. Leer/verificar antes del commit.
4. Programar `CMIT` y verificar otra vez. No borrar la copia anterior al terminar.
5. En el próximo montaje, elegir el banco válido más nuevo. Dos bancos válidos
   deben tener generaciones consecutivas, incluido el rollover `ffffffff→0`.
   Generaciones iguales/no adyacentes son un error, no una elección arbitraria.

Si ninguno es válido, se usan los defaults, sin escribir automáticamente.
Un error de lectura **no** se interpreta como almacenamiento vacío. Tras un
fallo de I/O se invalida el estado RAM y se exige montar de nuevo: perder el ACK
del commit puede significar que la edición sí llegó a almacenamiento.

La unidad de atomicidad es **una llamada de edición**, no la carga completa de
varios paquetes desde una GUI. Una carga interrumpida entre paquetes puede dejar
un prefijo de ediciones ya confirmado. No se implementa todavía el adaptador de
escritura VIA/Vial ni un mecanismo de desbloqueo.

## Pruebas y medición

**62 tests totales pasan en macOS y Linux**,12 nuevos para este almacén:

- Defaults reales, cambios de banco, offsets impares, no-op, límites y rechazo
  de posiciones/keycodes no permitidos antes de cualquier mutación.
- CRC contrastado independientemente con `zlib.crc32`, formato desconocido,
  corrupción, generaciones ambiguas y rollover.
- **29.266 escenarios de fallos**: desde defaults y desde cada banco activo;
  cada punto de programación con0..32 bits completados, cada prefijo de borrado
  de0..1024 B y cada fallo de lectura. Tras reiniciar se exige exactamente el
  mapa anterior o el nuevo, nunca una mezcla dentro de la transacción, y que
  el banco activo anterior no haya cambiado.
- Reintento después de fallo, backend que afirma éxito sin escribir,250
  ediciones aleatorias contra un modelo y los mismos cortes bajo ASan/UBSan.

El modelo permite daño parcial solo en la palabra/banco seleccionado. No cubre
caídas de tensión que dañen otros bancos, desgaste, tiempos eléctricos, cachés,
ejecución mientras se programa flash ni errores reales del controlador Sonix.
No son29.266 cortes de alimentación del teclado: **todo es simulación**.

Con el GCC ARM fijado, `-mcpu=cortex-m0 -mthumb -Os`, el **objeto independiente**
ocupa1272 B de `.text`,0 B de `.data` y0 B de `.bss`. Estado explícito8 B.
Los frames estáticos reportados incluyen64 B para `alloy_map_patch`,40 B para
`check_bank` y20 B para CRC; son **por función**, no sumas de cadena de llamadas
ni máximos en ejecución. No sumar solo8 B a1952 B y declarar estable el firmware:
falta enlazar adaptadores, conocer sus pilas y medir USB/escaneo reales.

```sh
rtk proxy python3 -B -m unittest discover -s tests -v
# Solo Linux, toolchain ya preparado; no crea imagen instalable:
rtk proxy python3 -B scripts/measure_map_store.py
rtk proxy python3 scripts/check_port_readiness.py
```

Los manifiestos con rutas de build quedan ignorados en `build/map-store/` y
`artifacts/analysis/`; no se amplió la whitelist pública. El checklist sigue
devolviendo **2 / NOT READY TO FLASH**.

## Próximo trabajo difícil

1. Sustentar geometría, regiones preservadas, reglas de programación/borrado,
   ejecución desde flash y recuperación con carcasa cerrada. No implementar
   escrituras físicas con el tamaño virtual como si fuera un dato del MCU.
2. Evaluar desgaste/latencia: este diseño simple reescribe el mapa completo por
   edición (hasta230 llamadas mutadoras simuladas). Una carga de32 paquetes
   distintos puede borrar32 bancos. Necesita una estrategia de desgaste y
   coordinación con USB antes de usarse en hardware; no se promete vida útil.
3. Adaptador de lectura dinámica al escaneo QMK, política completa de keycodes,
   protocolo de edición y seguridad/desbloqueo. Mantener el READ-ONLY actual
   hasta que el camino real sea verificable; nunca anunciar persistencia RAM.
4. Enlace completo, máximo de pila, estabilidad y finalmente detección, remapeo
   y retención del mapa en Vial con el teclado físico. **Objetivo aún pendiente.**
