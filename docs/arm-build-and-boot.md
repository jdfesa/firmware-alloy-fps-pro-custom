# Compilación ARM real y revisión de arranque — 2026-10-29

> [!NOTE]
> Informe de una fase anterior, conservado por su evidencia y fuentes. No usar
> sus estados provisionales como estado actual ni sus comandos como receta universal.
> Leer primero [README](../README.md), [estado](status-and-limits.md) y
> [seguridad/recuperación](safety-and-recovery.md).

> Informe histórico del primer build. Actualización posterior: [ISP real,
> jumploader propio y variante custom42_fn](usb-isp-and-startup.md).


## Resultado

Se compilaron y enlazaron **dos candidatos nativos ARM Cortex-M0** desde el port experimental, sin abrir la carcasa ni acceder a entradas o configuración del Silakka54. No se flasheó el HyperX y no se probó estabilidad en hardware.

| Candidato | Binario de aplicación | Flash disponible para la app |
| --- | ---: | ---: |
| `custom42` — 42 posiciones, BASE/NUM/SYM/NAV | 17316 B | 30208 B |
| `default` — 87 teclas de referencia | 16868 B | 30208 B |

Ambos incluyen **Bootmagic sobre Escape físico `[0,0]` al encender**, pensado para volver al cargador si el candidato arranca y su matriz funciona. En `custom42`, Escape puede seguir deshabilitado como tecla de uso normal: Bootmagic lee la matriz antes del mapa. **No rescata una aplicación que no llega a arrancar o cuyo escaneo no funciona.**

Los `.elf`, `.hex`, `.bin` y manifiestos se guardan localmente en `build/custom42/` y `build/default/` (excluidos del versionado). Los manifiestos y logs de evidencia también están en `artifacts/analysis/arm-build-*.json` y `.log`. Los hashes definitivos se consultan en esos manifiestos, no se deducen del nombre del archivo.

## RAM: cabe, pero no demuestra estabilidad

El ELF de ambos candidatos reserva estáticamente:

- `.data`: 280 B; `.bss`: 972 B.
- Pila de interrupciones: 224 B; pila de proceso: 480 B.
- Total anterior: 1956 B; con alineación hasta el heap: **1960 de 2048 B**.
- Heap restante: **88 B**.

Las pilas anteriores ya están reservadas dentro de esos 1960 B. El heap no es una medida de margen de pila y no se midieron máximos de uso en ejecución. No se redujeron pilas a ciegas para forzar que el enlace pase. No hay evidencia para llamar estable al candidato ni para habilitar Vial todavía.

## Detalle crítico: la aplicación empieza en `0x200`, no en cero

El [linker de la plataforma fijada](https://github.com/SonixQMK/ChibiOS-Contrib/blob/4b5588b511c0e98b4ae8c3b81357e4468ec9d1cb/os/common/startup/ARMCMx/compilers/GCC/ld/SN32F260.ld) define:

- Aplicación: inicio `0x00000200`, longitud 30208 B, límite exclusivo `0x7800`.
- RAM: `0x20000000–0x200007ff`.
- Vectores de interrupción de la aplicación: alineados a 512 B y presentes en `0x200`.

Su comentario explica la dependencia del **jumploader de SonixQMK**. El `.bin` generado comienza con los bytes correspondientes a `0x200`; **no contiene una imagen completa para escribir desde `0x0`**. El driver de build lo nombra `candidate-offset-0x200.bin` para que esto no se pierda.

La aplicación original extraída tiene sus vectores en `0x0`. Conservar sus primeros 512 B y escribir QMK desde `0x200` **tampoco está demostrado que funcione**: el arranque original puede depender de código o tablas reemplazados. Antes de escribir hay que validar un arranque auxiliar compatible y una forma de recuperación con carcasa cerrada.

La dirección de salto al cargador usada por esta plataforma, `SN32_BOOTLOADER_ADDRESS=0x1FFF0009`, es otra cosa: no es la dirección de carga de la aplicación. Instalar el jumploader ocupa el arranque de la aplicación, aunque no equivalga a reemplazar el cargador ROM/ISP. Sigue siendo una escritura que requiere revisión.

**No se preparó imagen combinada, no se instaló jumploader y no se incluye una orden de flasheo.** No usar tampoco el binario rellenado `*.analysis-only.bin` del proveedor como restauración.

## Entorno de build aislado

- SonixQMK `62973ee48a976c6f7cc6d4f7b198bd48a2fdfe60`.
- ChibiOS `6170ddf92d55be54c89b708d1882eea229edeb2c`.
- ChibiOS-Contrib `4b5588b511c0e98b4ae8c3b81357e4468ec9d1cb`.
- LUFA `549b97320d515bfca2f95c145a67bd13be968faa` y printf `c2e3b4e10d281e7f0f694d3ecbd9f320977288cc`.
- [xPack GNU Arm GCC 12.3.1-1.2](https://github.com/xpack-dev-tools/arm-none-eabi-gcc-xpack/releases/tag/v12.3.1-1.2), archivo publicado y SHA-256 verificados antes de extraer. Todo dentro de `artifacts/tools`, sin instalación global.

`toolchains/build-lock.json` registra las revisiones, fuentes Python y checksum del compilador. PyPI no fue accesible por DNS, por lo que se usaron fuentes de sus repositorios primarios. `platformdirs` requiere un archivo de versión normalmente generado por hatch-vcs: se generó localmente desde su tag 4.3.6, sin modificar algoritmos de la librería.

`scripts/qmk_build_cli.py` es un **cargador solo de comandos de build**: utiliza los generadores y validadores de esquema reales de upstream, sin reimplementarlos ni omitir validaciones. Evita el registro general de comandos que exigiría dependencias de USB o imágenes no usadas aquí. No registra comandos de flasheo, instalación ni configuración; fuerza rutas de configuración/userspace dentro del proyecto. GNU Make, fuentes C, ChibiOS y enlazador son los de las revisiones fijadas.

Se corrigió una opción de la fuente inicial: `VIAL_ENABLE=no` no es válida en SonixQMK y fue retirada. No se ha integrado Vial; `VIA_ENABLE=no` sigue deshabilitando VIA. LUFA es necesario incluso en este build ARM porque aporta definiciones comunes HID.

Con el entorno local preparado:

```sh
rtk proxy python3 scripts/build_firmware.py --keymap custom42
rtk proxy python3 scripts/build_firmware.py --keymap default
rtk proxy python3 -m unittest discover -s tests -v
rtk proxy python3 scripts/check_port_readiness.py
```

El driver revisa commits, rechaza cambios rastreados en fuentes upstream, usa el Makefile principal y guarda logs completos, hashes y mapa de memoria. Solo acepta `default` y `custom42`; no expone un target `flash`. El comprobador de estado sigue saliendo con código **2**. El indicador ARM aprobado significa **build y ajuste estático al enlazador**, no pruebas de hardware.

## Por qué todavía no se hizo la prueba física

1. **El entorno no expone `/dev/bus/usb`, `/dev/hidraw*` ni `/dev/input`**; solo hay metadatos sysfs. No se dispone aquí de acceso directo para hablar con el HyperX, entrar/salir del cargador o escribirlo.
2. La revisión/polaridad de matriz y la recuperación del original siguen sin validar en la unidad.
3. El arranque auxiliar requerido por el candidato todavía no está validado. La autorización general del usuario para experimentar no cambia el offset ni demuestra recuperabilidad.

El siguiente hito es revisar el jumploader/protocolo y conseguir una sesión de prueba con USB accesible de forma autorizada, manteniendo la carcasa cerrada. **Ningún teclado ha sido modificado.**
