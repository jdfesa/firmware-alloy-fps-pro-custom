# Identificación del HyperX

> [!NOTE]
> Informe de una fase anterior, conservado por su evidencia y fuentes. No usar
> sus estados provisionales como estado actual ni sus comandos como receta universal.
> Leer primero [README](../README.md), [estado](status-and-limits.md) y
> [seguridad/recuperación](safety-and-recovery.md).

Actualizado: 2026-10-29. La carcasa debe permanecer cerrada por decisión explícita del usuario. Identificación e inferencia estática, no validación en hardware.

## Evidencia de la unidad del usuario

### Etiqueta inferior fotografiada

| Campo | Lectura de la foto |
| --- | --- |
| Nombre | Alloy FPS Pro |
| Modelo / SKU | `HX-KB4RD1-US` |
| Referencia de etiqueta/producto | `3500241-001.A02LF` |
| Alimentación nominal | `5 V CC / 500 mA` |

La foto recibida permite leer estos campos con claridad. **No permite ver el microcontrolador ni la revisión de la placa interna.** No asumir que `A02LF` es la revisión de PCB. El sufijo `US` no sustituye una foto superior para verificar la distribución real y sus leyendas.

Por privacidad no se transcriben números `SN`, `SP` ni el código matricial. La foto original no se copió al proyecto. Si se necesita publicar evidencia visual, preparar primero una versión que oculte esos identificadores.

### Identidad USB observada en la primera fase

| Campo | Valor |
| --- | --- |
| Fabricante | `Kingston` |
| Producto | `HyperX Alloy FPS Pro Mechanical Gaming Keyboard` |
| VID:PID | `0951:16d2` |
| `bcdDevice` | `2112` |
| Interfaces | 3 HID |

Fuente: archivos sysfs, sin abrir dispositivos de entrada ni enviar comandos al teclado. Ruta de esa lectura: `/sys/bus/usb/devices/1-6`, no estable al reconectar. La fotografía y los descriptores concuerdan en el nombre del modelo; no bastan para establecer revisión electrónica o versión exacta del firmware.

## Evidencia externa, no confirmación de esta unidad

Un [desmontaje del FPS Pro](https://www.tweaktown.com/reviews/8405/hyperx-alloy-fps-pro-mechanical-gaming-keyboard-review/index.html) muestra `SN32F268FG`. La imagen de actualización extraída presenta vectores Cortex-M0, direcciones de periféricos compatibles y un updater con cadena `SN32F26x`; su descriptor USB coincide con el conectado en `0951:16d2`, `bcdDevice=2112`. Es una inferencia coherente, no una identificación física del chip del usuario. Ver [evidencia y límites](closed-case-development.md).

## Datos que faltan

- Revisión electrónica exacta, a contrastar sin desmontar; no volver a solicitar fotos internas.
- La matriz está inferida en `hardware/matrix-inference.json`; faltan validación de comportamiento/polaridad y estudio de LEDs.
- Método de acceso a lectura/recuperación de esta revisión y estado de protección, sin modificarlo para averiguarlo.
- Confirmación deliberada de las cinco teclas averiadas y estabilidad del resto, exclusivamente en el HyperX.

El Silakka54 y su configuración quedan fuera de esta investigación.
