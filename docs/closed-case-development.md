# Desarrollo con carcasa cerrada — 2026-10-29

> [!NOTE]
> Informe de una fase anterior, conservado por su evidencia y fuentes. No usar
> sus estados provisionales como estado actual ni sus comandos como receta universal.
> Leer primero [README](../README.md), [estado](status-and-limits.md) y
> [seguridad/recuperación](safety-and-recovery.md).

## Restricción y alcance

El usuario **no abrirá el HyperX** y autoriza avanzar cuidadosamente con un firmware personalizado. Se reemplaza la propuesta de fotos internas por investigación de archivos, metadatos USB y protocolo cuando sea accesible. El Silakka54 sigue excluido de toda operación.

## Paquete adquirido, aún no autenticado

Se encontró una copia de `HyperX_Alloy_FPS_Pro_Keyboard_Firmware_Updater_v2112.zip` en [IRus/blog, commit fijado](https://github.com/IRus/blog/tree/f280a57181cb8166c1031d064869fa83d3f0d5a9/content/posts/archive/hyperx-alloy-fps). Es un **espejo de terceros**, no un archivo autenticado obtenido del servidor del fabricante.

| Artefacto | Tamaño / SHA-256 |
| --- | --- |
| ZIP | 933067 B; `d023babeea8fb4305d727fe550f9bdc57e9a1fc82fe909b9072cbb066a297a6e` |
| EXE contenido | 2243096 B; `c192c4a2e678d416778b0dd042abb215489f8dba4e20e9130d43904d144ceada` |
| Recurso comprimido | 94922 B; `045dc26ec2159eff8200e121eb1694adf668d8b3908c53993ad963fbfcb9f4b5` |
| HEX extraído | `560d61f2748ce9b2fd0cc9f93dc73350fd85ddcaab04f8d0c095b0d2ad1ba56d` |

REA inventarió el ZIP (`ev_639661a1355add344a8238486e99d48ce2efe971af62984c42d40c68cc5b094b`) y los recursos PE (`ev_92b2a7f1bc47af8ad6b24984ddf3af14a384cfc10c902e3a6dd3f10f2795ae28`). El EXE es nativo x86, no .NET. No se ejecutaron EXE/DLL ni se enviaron comandos a los teclados.

### Extracción reproducible

El recurso PE tipo `RAR`, nombre numérico 140, offset `1511564`, tamaño `94922`, **no es un archivo RAR**: contiene tres enteros little-endian `(74323,166912,94910)` y zlib desde el byte 12. La salida son un Intel HEX de 74323 B y una DLL de 166912 B. `scripts/vendor_image.py` fija hashes, comprueba límites y valida registros/checksums HEX antes de producir archivos.

El HEX solo contiene `0x0000–0x6717` y `0x77fc–0x77ff`. **No contiene el bootloader `0x7800–0x7fff`**. El archivo `artifacts/analysis/FPS_Pro_v2112.analysis-only.bin` rellena huecos con `FF` para análisis; esos bytes no fueron extraídos de un teclado. **No usarlo como imagen de restauración ni flashearlo.**

La imagen incluye vectores Cortex-M0, cadenas Kingston / HyperX Alloy FPS Pro y el descriptor USB en `0x5b30`: VID `0951`, PID `16d2`, bcdDevice `2112`, consistentes con los metadatos observados. No demuestran que el contenido de la flash de esta unidad sea idéntico.

## Reconstrucción estática de matriz

Ghidra vía REA no estaba disponible (`GHIDRA_INSTALL_DIR` sin configurar). No se cambió la configuración ni se instalaron motores globales. Se compiló **Capstone 5.0.6**, solo ARM, dentro de `artifacts/tools`; fuente y checksum de la [release primaria](https://github.com/capstone-engine/capstone/releases/tag/5.0.6). Lo siguiente deriva de análisis ordinario Python/Capstone, no de una decompilación REA ni de ejecución del firmware.

| Evidencia estática | Observación / inferencia |
| --- | --- |
| Rutina `0x288c`, límite `0x2968` | Recorre 14 selectores de fila, muestrea 8 bits, invierte el valor leído. |
| Tabla `0x5d88`, 14 registros de 12 B | Filas: `C0 C1 C2 A12 A13 A14 A15 D0 D1 D2 D3 D4 C3 C4`. A/C/D son alias de puertos GPIO 0/2/3 del MCU candidato. |
| Lectura GPIO0 en `0x28e6–0x290a` | Columnas: `A0 A1 A2 A3 A7 A8 A9 A10`. Activo bajo; `COL2ROW` es una inferencia de escaneo a validar. |
| Tabla `0x5ed6` | 14 × 8 códigos u16, con valores especiales OEM. |
| Máscaras `0x5e30`, tabla `0x5e58`, rutinas `0x254e/0x2438` | Decodifican los especiales a sus códigos primarios. Resultado: 87 teclas. Up tiene código crudo cero en `[13,0]` y flag especial: **no es un hueco**. |
| Fila eléctrica 7, `D0` | Incluye `8 9 0 - =`, Backspace e Insert. Consistente con el patrón de avería reportado, no diagnóstico de la pista de la unidad. |

`scripts/infer_matrix.py` vincula esta interpretación al hash exacto de la imagen y genera `hardware/matrix-inference.json`. El chip SN32F268F y el pinout son **inferencias estáticas fundadas**, aún no validadas en esta revisión conectada.

## Código y pruebas creados

Ver [fuentes QMK y capas](../firmware/README.md). El generador produce un mapa completo de referencia y otro con 42 posiciones, BASE/NUM/SYM/NAV, sin iluminación ni Vial inicial. La distribución es provisional: no se leyó el Silakka54.

**17 pruebas locales pasan**, incluidas tablas C compiladas y verificadas con GCC anfitrión. Por separado, ya se compilaron y enlazaron dos candidatos reales QMK/ARM con el compilador y dependencias aislados en el proyecto. `custom42` ocupa 17316 B y `default` 16868 B; ambos reservan 1960 B de los 2048 B de RAM, incluidas las pilas, y dejan 88 B de heap. No se midió uso máximo de pila ni estabilidad; no hay firmware instalado.

El [informe de build y arranque](arm-build-and-boot.md) documenta una condición crítica: la aplicación se enlaza en `0x200` y requiere jumploader, no basta con escribir un binario desde cero. `hardware/validation-status.json` marca aprobado únicamente el build/ajuste estático ARM; mantiene pendientes revisión, comportamiento de matriz, bootloader, recuperación original y jumploader. `scripts/check_port_readiness.py` sale con código 2. No se agregó herramienta de flasheo ni se modificó ningún teclado.

## Siguiente trabajo sin desmontaje

1. Revisar el jumploader y la transición desde el arranque OEM; los candidatos ARM y su memoria estática ya están documentados. No preparar una imagen combinada sin validar recuperación y límites de escritura.
2. Estudiar el protocolo de actualización de la DLL/firmware sin ejecutarlos. No confundir una orden `ReadData` de librería con una capacidad de dump comprobada.
3. Determinar entrada y recuperación del bootloader aplicables a esta revisión por evidencia estática/USB, sin quitar protección ni probar escrituras a ciegas. El entorno actual no expone nodos `/dev/input`, `/dev/hidraw*` ni `/dev/bus/usb`; sysfs sí proporciona metadatos.
4. Validar posteriormente el candidato en el HyperX, sin involucrar Silakka54. No etiquetarlo como estable antes de estas pruebas.
