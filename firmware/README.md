# Port nativo experimental — compilado, no instalado ni estable

Actualización: [consulta ISP real y jumploader compilado](../docs/usb-isp-and-startup.md).
`custom42_fn` ofrece 42 posiciones + F1–F12 directas en todas las capas,
17316 B y el mismo uso estático de RAM. El mapa estricto `custom42` no cambia.
26 tests pasan. Ningún candidato fue flasheado.

Se creó `keyboards/hyperx/alloy_fps_pro` para la base **SonixQMK**, referencia de código `62973ee48a976c6f7cc6d4f7b198bd48a2fdfe60`. Los dos mapas se compilaron y enlazaron para ARM Cortex-M0. Se comprobó su ajuste estático a flash/RAM, pero no se probaron en el teclado. **Los binarios no están aprobados para flashear.** Ver [build, memoria y arranque](../docs/arm-build-and-boot.md).

- MCU **inferido**: SN32F268F; matriz reconstruida estáticamente de 14 × 8.
- `default`: mapa completo de 87 teclas. Fn activa una capa transparente de referencia, sin replicar funciones OEM de iluminación.
- `custom42`: 42 posiciones, cuatro capas BASE / NUM / SYM / NAV. No es una copia de la configuración del Silakka54, a la que no se accedió.
- Mantener RAlt para NUM y Fn para SYM. Caps: toque Escape, mantener NAV. En NAV, H/J/K/L son flechas; I es Backspace. Números sobre Q–P en NUM; símbolos US sobre Q–P en SYM.
- Todas las posiciones no seleccionadas, incluidas las cinco averiadas, son `KC_NO` en las cuatro capas. El mapa por defecto de 87 teclas sí las representa como referencia.
- Vial/VIA, iluminación y almacenamiento persistente deshabilitados inicialmente. `EEPROM_DRIVER=transient` evita diseñar escrituras de configuración sobre flash de geometría aún no validada. No promete preservar ajustes OEM si se flashea.
- USB experimental `FEED:A11F`, distinto del HyperX original y del Silakka54. No implica VID registrado para distribución comercial.
- El layout JSON representa la **rejilla eléctrica**, no la geometría física TKL; no es una definición Vial.
- Bootmagic sobre Escape físico `[0,0]` al encender: permite intentar volver al cargador solo si la aplicación arranca y la matriz funciona; no es recuperación garantizada.

## Regeneración y pruebas locales sin hardware

Con la imagen de distribución disponible localmente (ver [evidencia](../docs/closed-case-development.md)):

```sh
rtk proxy python3 scripts/vendor_image.py artifacts/vendor/HyperX_Alloy_FPS_Pro_Keyboard_Firmware_Updater_v2112.zip
rtk proxy python3 scripts/infer_matrix.py
rtk proxy python3 scripts/generate_qmk.py
rtk proxy python3 -m unittest discover -s tests -v
rtk proxy python3 scripts/check_port_readiness.py
```

La última orden debe salir con código **2 / NOT READY TO FLASH** mientras falte validación. Pasan 26 pruebas. Las pruebas C de esa suite usan GCC del anfitrión y un encabezado mínimo: verifican sintaxis y datos de tablas, **no sustituyen el build real QMK/ARM** ejecutado por separado, ni prueban USB, escaneo, debounce, tap/hold o consumo de pila en ejecución.

## Build ARM local sin tocar dispositivos

Con el checkout y herramientas aislados ya preparados en `artifacts/tools`:

```sh
rtk proxy python3 scripts/build_firmware.py --keymap custom42
rtk proxy python3 scripts/build_firmware.py --keymap default
```

El driver solo compila y analiza; no abre USB ni admite targets de flasheo. Revisiones de dependencias en `toolchains/build-lock.json`, resultados en `build/{custom42,default}/` y evidencia en `artifacts/analysis/arm-build-*.json`.

| Mapa | Aplicación | RAM reservada hasta heap | Heap |
| --- | ---: | ---: | ---: |
| `custom42` | 17316 B | 1960 / 2048 B | 88 B |
| `default` | 16868 B | 1960 / 2048 B | 88 B |

La RAM reservada incluye pilas IRQ/proceso de 224/480 B; **no se midió su máximo de uso**. La aplicación comienza en `0x200` y necesita el jumploader de la plataforma, que no se instaló ni validó. El archivo `candidate-offset-0x200.bin` **no es una imagen completa para escribir desde cero**. No se incluye instalador ni comando de flasheo.

Antes de escribir: contrastar revisión cerrada por USB/protocolo, entrada y salida de bootloader, jumploader, recuperación original, rangos de flash y comportamiento de matriz. El entorno SSH permite consultar ISP; la consulta y retorno OEM ya se verificaron, no el rescate tras escribir un firmware incorrecto. No cambiar protección de lectura. No abrir la carcasa: el usuario lo descartó expresamente.
