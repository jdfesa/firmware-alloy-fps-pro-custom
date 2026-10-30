# Vial: presupuesto real y pendientes

Estado: **2026-10-29**. No hay firmware Vial instalado ni integración completa.
El repositorio consolidado conserva el puerto QMK previo y sus resultados.

**Actualización:** el parche compacto preexistente ya elimina el overflow del
transporte. El nuevo [prototipo de lectura](vial-readonly-prototype.md) enlaza
sin aumentar la RAM estática, pero no añade remapeo ni persistencia.

**Avance posterior:** [almacén C simulado](vial-map-store.md) con estado8 B y
sin sombra RAM del mapa; objeto ARM1272 B, fuera del enlace del candidato.
No se ha medido todavía el coste del firmware integrado ni existe backend físico.

## La iluminación ya está desactivada

`firmware/keyboards/hyperx/alloy_fps_pro/rules.mk` desactiva backlight,
RGBLIGHT, RGB_MATRIX y LED_MATRIX. Los tamaños siguientes ya incluyen ese
recorte. Apagar físicamente los LED no convierte su consumo eléctrico en RAM;
lo que puede ahorrar memoria es quitar su controlador de software.

## Mediciones reproducibles, sin dispositivo

Revisión SonixQMK: `62973ee48a976c6f7cc6d4f7b198bd48a2fdfe60`.
MCU configurado: SN32F268F, RAM de 2048 B. No cambia la inferencia pendiente de
encapsulado/revisión exacta de esta unidad. Pilas reservadas: IRQ224 + proceso480.

| Variante | RAM reservada / posición final del linker | Resultado |
| --- | ---: | --- |
| custom42_fn, sin Raw HID | 1960 B | Enlaza;88 B antes del final RAM |
| Raw HID, colas entrada/salida1 y teclado1 | 2392 B | No enlaza;344 B de exceso |
| Anterior, sin tapping/oneshot y serial constante | 2240 B | No enlaza;192 B de exceso |
| `raw_compact`, parche const + reportes32 B | 1952 B | Enlaza;96 B heap, tapping y cuatro capas |
| `vial_readonly`, protocolo de lectura sobre compacto | 1952 B | Enlaza;96 B heap, no edición/persistencia |

La variante mínima es **solo una medición**: deshabilitar tapping rompe la
función de mantener Caps para NAV del `LT(NAV, KC_ESC)`. No es un mapa usable.
No se redujeron pilas ni se falseó el límite del linker; consumo máximo de pila
sin medir. Estas variantes todavía **no incluyen Vial ni un mapa editable**.

Reproducir en Linux, con el entorno fijado preparado:

```sh
rtk proxy python3 -B scripts/measure_raw_hid.py
```

El script valida revisiones/upstream sin cambios, prepara dos mapas temporales
bajo `artifacts/tools/qmk`, compila y registra `artifacts/analysis/raw-hid-budget.json`.
Un overflow reconocido es resultado del experimento, no éxito de firmware.
Errores ajenos al patrón RAM provocan fallo del script. No contiene operaciones
USB, borrado, desprotección ni flasheo. Logs e imágenes siguen ignorados por Git.
La ejecución real por SSH reprodujo ambas cifras;30 tests locales pasan.

## ¿Ayudan tres capas en lugar de cuatro?

El usuario acepta considerar tres como alternativa si hace viable Vial.
No se modificaron aún las cuatro capas existentes.

- El mapa QMK fijo es `const ... PROGMEM`: quitar una capa reduce flash, no
  libera el RAM que hoy falta para Raw HID.
- Un mapa editable completo14×8×2 B consume224 B por capa **si se guarda en RAM**:
  cuatro896 B, tres672 B. Ahorrar25% de ese mapa es útil, pero ese almacenamiento
  todavía no está incluido en el exceso de192 B medido.
- Un almacenamiento persistente debe evitar duplicar innecesariamente el mapa
  en RAM. Necesita diseño de escritura/borrado seguro, límites y pruebas frente
  a corte de energía. No se implementó ni validó aún.

El primer recorte de RAM del transporte ya está implementado en el parche
compacto, sin reducir pilas; comportamiento USB real aún pendiente. Siguiente
hito: mapa editable y persistencia con pruebas frente a cortes, sin duplicar
el mapa en RAM. Que el enlace quepa no demuestra estabilidad en hardware.

## Referencias de protocolo revisadas

Se inspeccionó fuente oficial, guardada localmente como referencia ignorada:

- [vial-qmk dd43959: protocolo](https://github.com/vial-kb/vial-qmk/blob/dd43959ae5c08d8a28d38a1acf7b04e86b14a344/quantum/vial.c): Vial6, paquetes32 B, identidad y bloques de definición.
- [Generador de definición](https://github.com/vial-kb/vial-qmk/blob/dd43959ae5c08d8a28d38a1acf7b04e86b14a344/util/vial_generate_definition.py): JSON compacto comprimido con LZMA/XZ.
- [vial-gui aef8222: consumidor](https://github.com/vial-kb/vial-gui/blob/aef8222a2d0429a183b2ed692d5f9efcfd383f08/src/main/python/protocol/keyboard_comm.py): VIA9, descarga de definición y lectura/remapeo.

Se añadió un módulo **de lectura** en `keymaps/vial_readonly`, con protocolo y
definición probados en host; no se probó detección por Vial ni escritura de mapas.
Activar `VIAL_ENABLE` en la base SonixQMK actual no incorpora ese firmware.

## No es el único impedimento

Además de memoria/protocolo/persistencia, siguen pendientes:

1. Matriz inferida: validar teclas reales y combinaciones en esta unidad.
2. Arranque de aplicación en0x200 con jumploader: compilado, no probado.
3. Recuperación con carcasa cerrada ante aplicación inválida y restauración
   original. Volver de ISP al OEM sano no demuestra esas recuperaciones.
4. Estabilidad y máximo real de pila, reinicios y conservación de mapas.

No se alteró `hardware/validation-status.json` para sortear estos requisitos.
