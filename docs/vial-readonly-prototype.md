# Prototipo de lectura Vial: código y límites

**2026-10-29. Compilado para ARM, no instalado.** `vial_readonly` implementa
un subconjunto de lectura de **Vial 6 / VIA 9** encima del parche USB compacto
ya existente. No es el port completo de Vial-QMK, no permite configurar teclas
y no demuestra que Vial lo detecte en hardware.

## Qué se implementó

En `firmware/keyboards/hyperx/alloy_fps_pro/keymaps/vial_readonly/`:

- `protocol.c/.h`: parser C independiente, paquetes de exactamente 32 B,
  respuesta sobre el mismo buffer, sin heap ni mapa adicional en RAM.
- `keymap.c`: adapta Raw HID y lee el mapa compilado `custom42_fn`. Conserva
  42+12 posiciones, cuatro capas y `LT(NAV, KC_ESC)`. Hay aserciones estáticas
  de dimensiones y de los códigos MO/LT/Shift usados, frente a las revisiones
  fijadas. No se afirma compatibilidad con todos los keycodes de otros forks.
- `vial.json` y `definition.h`: definición comprimida XZ en flash, generada
  desde la misma matriz/mapa. Muestra 54 posiciones en **cuadrícula eléctrica**,
  no pretende ser un dibujo de la geometría física TKL ni del Silakka54.
- `config.h` y `rules.mk`: conservan el transporte compacto y anuncian
  **READ-ONLY** tanto en el producto USB como en la definición. No habilitan
  `VIA_ENABLE`/`VIAL_ENABLE` ni almacenamiento persistente.

El UID de ocho bytes es un identificador experimental de este diseño, **no el
número de serie de la unidad**. VID/PID experimental sigue siendo `FEED:A11F`;
no se afirma una asignación oficial.

## Superficie de protocolo

| Consulta | Respuesta |
| --- | --- |
| VIA versión / cantidad de capas | 9 / 4 |
| Vial identidad / tamaño / bloques de definición | Versión 6, UID de diseño, XZ paginado32 B |
| Lectura de tecla y buffer de mapa | Mapa compilado completo896 B, keycodes big-endian, sin copiarlo entero a RAM |
| Macros / settings / funciones dinámicas | Cero macros, cero entradas, sin settings |
| Estado de desbloqueo | Siempre bloqueado, sin combinación de desbloqueo |
| Opciones de distribución | Valor fijo0 |

**Se rechazan** SET_KEYCODE, SET_BUFFER, reset de mapas/EEPROM, cambios de
iluminación, macros, encoders, unlock y salto a ISP/bootloader. Tampoco se
expone el estado de interruptores ni se leen pulsaciones. Comandos desconocidos
o índices inválidos devuelven `ff` +31 ceros. Paquetes mal dimensionados no
reciben respuesta. Los últimos bloques se rellenan con cero; se rechazan páginas
fuera de rango y un word alto de página que de otro modo se truncaría.

**Advertencia importante:** la GUI revisada envía SET_KEYCODE sin comprobar el
resultado antes de actualizar su vista. Puede aparentar una edición que este
firmware rechaza. Por eso no debe usarse como configurador: el nombre READ-ONLY
es deliberado, y una futura prueba debe limitarse a descubrimiento/lectura y
confirmar el mapa por readback. No se implementó una persistencia ficticia en RAM.

## Evidencia reproducible

Build real con los commits/GCC fijados en `toolchains/build-lock.json`:

| Variante | App flash | RAM reservada, incluidas pilas | Heap restante |
| --- | ---: | ---: | ---: |
| `raw_compact` preexistente | 18536 B | 1952/2048 B | 96 B |
| `vial_readonly` nuevo | **19460 B** | **1952/2048 B** | **96 B** |

`.data`388 B, `.bss`852 B; pilas IRQ224/proceso480 B sin reducir. La definición
336 B y el mapa896 B están en sección de solo lectura del ELF. El heap restante
**no es una medición del margen de pila**. No se midieron máximos de pila,
latencia, reenumeración ni estabilidad real.

SHA-256 de `candidate-offset-0x200.bin`:
`c178ac79ebde898a74487f327aff7c18fdf366cf78fbb4cff717bad998188262`.
La aplicación sigue en **0x200**, requiere jumploader compatible y no es una
imagen para escribir desde cero. Manifiesto: `build/vial_readonly/build-manifest.json`;
logs/mapas: `artifacts/analysis/vial-readonly*`. Todos siguen excluidos de Git.

La suite pasa **50 pruebas en Linux y macOS**. Las once nuevas comprueban la
secuencia de consultas usada por la GUI (simulada, no la GUI ejecutándose),
descompresión de la definición,896 B de las cuatro capas, offsets impares,
límites, exclusión de teclas averiadas, longitudes0..255 y rechazo de todas las
mutaciones. El C del parser y adaptador real se compila en host; ASan/UBSan
recorren65.536 combinaciones de comando/subcomando con canarios de memoria.
Estas pruebas **no simulan el MCU, la pila USB ni el almacenamiento flash**.

Comandos, sin USB:

```sh
rtk proxy python3 -B scripts/generate_vial_readonly.py --check
rtk proxy python3 -B -m unittest discover -s tests -v
rtk proxy python3 -B scripts/build_compact_raw.py --keymap vial_readonly
rtk proxy python3 scripts/check_port_readiness.py
```

El build ARM usa Linux y el entorno ya preparado; no reinstalarlo en macOS.
El driver solo admite `raw_compact` o `vial_readonly`, verifica las preimágenes
del parche y restaura upstream incluso si el build falla, sin descartar cambios
concurrentes. El checklist sigue saliendo con **2 / NOT READY TO FLASH**.

## Referencias y próximo código

Las fuentes de protocolo son primarias, con URLs/hashes en
`toolchains/vial-protocol-lock.json`:

- [Vial-QMK dd43959: protocolo](https://github.com/vial-kb/vial-qmk/blob/dd43959ae5c08d8a28d38a1acf7b04e86b14a344/quantum/vial.c),
  [VIA IDs](https://github.com/vial-kb/vial-qmk/blob/dd43959ae5c08d8a28d38a1acf7b04e86b14a344/quantum/via.h).
- [Generador XZ](https://github.com/vial-kb/vial-qmk/blob/dd43959ae5c08d8a28d38a1acf7b04e86b14a344/util/vial_generate_definition.py).
- [Vial GUI aef8222: lectura y SET_KEYCODE](https://github.com/vial-kb/vial-gui/blob/aef8222a2d0429a183b2ed692d5f9efcfd383f08/src/main/python/protocol/keyboard_comm.py).

Siguiente hito de código: almacenamiento editable **sin duplicar896 B en RAM**,
con formato versionado, límites, validación de keycodes, escritura/borrado y
pruebas frente a cortes de energía. No añadir una API de escritura física hasta
sustentar regiones/geometría/preservación del ISP. Un backend simulado puede
probarse antes, pero no debe anunciar persistencia real.

En paralelo sigue siendo obligatorio resolver arranque y recuperación con
carcasa cerrada **antes de instalar cualquier candidato**, incluido este. El
HyperX está en la máquina Linux local, según aclaró el usuario; el host macOS
por SSH contiene la fuente principal. No hizo falta mover el teclado, abrirlo,
enviar comandos USB ni intervenir el Silakka54 en esta etapa.
