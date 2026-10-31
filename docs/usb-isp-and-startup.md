# USB real, arranque auxiliar y preparación de instalación

> [!NOTE]
> Informe de una fase anterior, conservado por su evidencia y fuentes. No usar
> sus estados provisionales como estado actual ni sus comandos como receta universal.
> Leer primero [README](../README.md), [estado](status-and-limits.md) y
> [seguridad/recuperación](safety-and-recovery.md).

**2026-10-29 — avance experimental; todavía sin flasheo.** Este informe sustituye
la limitación anterior de acceso USB: trabajando por SSH, los nodos sí son
accesibles en el entorno de esa prueba. No se instaló ningún remapeador ni se
ejecutó el actualizador/DLL propietario.

## Resultado en la unidad conectada

1. Selección exclusiva del HyperX `0951:16d2`, revisión USB `2112`, interfaz 0.
2. Entrada temporal al ISP mediante un Feature report de 64 bytes, sin report ID.
3. ACK válido para `GET_FW_VERSION` y `GET_CHECKSUM`.
4. Respuesta de versión: familia `0x20`, chip `0x02`: **SN32F26x** según el
   protocolo de SonixFlasherC. No identifica por sí sola el encapsulado/SKU
   exacto SN32F268F ni la revisión de PCB. Word en offset12: `0x0002`,
   conservado sin interpretar como opciones de chip. Seguridad reportada: `0x0000` (**CS0**).
5. Checksum reportado: **`0x27d1`**. No es un volcado de memoria.
6. Enviado `RETURN_USER_MODE`; después volvió a enumerar como HyperX con el
   mismo descriptor HID. **Escritura humana posterior confirmada.**

No se enviaron órdenes de borrar, programar o cambiar protección. El primer
diagnóstico esperó solo un segundo tras salir y mostró `after: []`; una lectura
posterior confirmó el retorno. La herramienta ahora espera la reenumeración
con timeout acotado y no informa éxito si no observa el OEM. No se repitió el
ciclo innecesariamente para probar ese cambio: se cubrió con tests simulados.

**Alcance:** esto valida entrar/salir del ISP desde un OEM que funciona. NO
valida recuperar el teclado si se destruye el inicio de su aplicación.

## Herramienta acotada, no un flasher

`scripts/probe_hyperx.py` usa únicamente la biblioteca estándar de Python en
Linux. Sin argumentos solo lee metadatos sysfs. Nunca lee eventos de teclas.
Solo acepta el HyperX/ISP SN32F26x en el puerto físico seleccionado e interfaz
0; rechaza ambigüedad y verifica identidad al abrir el nodo. El transporte
permite exclusivamente entrada OEM y comandos `1`, `6`, `7`; no tiene API para
mandar comandos arbitrarios ni para cargar binarios.

Desde la raíz del proyecto en la máquina conectada:

```sh
rtk proxy python3 scripts/probe_hyperx.py
```

Para repetir deliberadamente la consulta, obtener el **puerto actual** de esa
salida; no copiar el número de otro equipo. Esta operación interrumpe
temporalmente el HyperX y requiere permiso sobre hidraw:

```sh
rtk proxy sudo python3 scripts/probe_hyperx.py --probe-cycle --port PUERTO_OBSERVADO
```

No guardar contraseñas en scripts, comandos de documentación ni Git. Si falla
el retorno, desconectar y reconectar **solo el HyperX** y volver a comprobar
metadatos/escritura. No reintentar protocolos desconocidos ni usar unlock.
Una respuesta USB correcta no sustituye comprobar que escribe.

## Evidencia estática y revisiones

- Imagen OEM con SHA-256 registrado en `hardware/matrix-inference.json`:
  `0x17cc` maneja SET_REPORT; `0x1486` verifica los dos words de entrada
  `0x5AA555AA`, `0xCC3300FF` y `0x14c4` llama a `0x17c`, que salta a
  `0x1FFF0009`. Coincide con la entrada del proyecto abierto.
- [SonixFlasherC, revisión 73f9fab8](https://github.com/SonixQMK/SonixFlasherC/tree/73f9fab8a82c5c4f91181d276676c8f936726925):
  `src/device.c`, `src/chip.c`, `src/hid_io.c`, `include/chip.h`.
  Su ruta de **flasheo** intenta bajar seguridad a CS0: no usarla sin auditar
  y eliminar ese riesgo. Aquí no se ejecutó SonixFlasherC.
- [Jumploader SonixQMK, revisión a41aa3da](https://github.com/SonixQMK/sonix-keyboard-bootloader/tree/a41aa3da663e2bf0c00a87b6adc8f45597707d9b):
  referencia de vectores delegados y escaneo de una tecla, no un binario
  compatible con el HyperX por compartir chip.
- [QMK fijado, sn32_dfu.c](https://github.com/SonixQMK/qmk_firmware/blob/62973ee48a976c6f7cc6d4f7b198bd48a2fdfe60/platforms/chibios/bootloaders/sn32_dfu.c):
  usa `0xDEADBEEF` en el último word de RAM. El jumploader upstream antiguo
  busca `bldr` en otra dirección. El código del proyecto usa el contrato QMK fijado.

### No confundir ReadData con leer flash

La DLL local exporta `SnxISP_ReadData` en RVA `0x3260`. El análisis estático
la sigue hasta `0x2bc0`, luego el thunk `0x74e8` y el import
`HidD_GetFeature`. Es recepción de un reporte HID; por sí sola **no demuestra
un comando de volcado de flash**. DLL SHA-256 en `artifacts/analysis/extraction.json`.
No se ejecutó ni se distribuye su desensamblado.

### La imagen de referencia todavía no es restauración

Aplicando la suma de words little-endian módulo 65536 del código abierto al
archivo de análisis rellenado con `FF`:

| Intervalo | Resultado |
| --- | --- |
| `[0, 0x6718)` | `0xc8ff` |
| `[0, 0x7800)` | `0xc08c` |
| `[0, 0x8000)` | `0xbc8c` |

Ninguno coincide con `0x27d1`. Sin confirmar el dominio/algoritmo del ISP y
los huecos de HEX, no diagnosticar esto como corrupción ni afirmar que el
firmware instalado es distinto byte a byte. **Tampoco afirmar que coinciden.**
Incluso una coincidencia de checksum de 16 bits no probaría identidad ni
autenticidad. El HEX no contiene el cargador y no es backup de esta unidad.

## Nuevo código de arranque: compilado, no probado en hardware

`firmware/jumploader/` contiene C + ensamblador Cortex-M0 propios:

- Vectores en cero; delegación de excepciones a la tabla QMK en `0x200`.
- Salto por MSP/PC de la aplicación, con validaciones de límites y alineación.
- Solicitud de ISP mediante magic de QMK; pila inicial `0x20000780` para
  evitar que el prólogo C pise el magic en `0x200007fc`.
- Lectura de Escape inferido `[0,0]`: C0 salida baja y A0 entrada pull-up.
  Restituye los registros GPIO antes de saltar. No toca D5/BOOT0 desconocido.
- Linker impide exceder 512 bytes y prohíbe `.data`/`.bss` que requerirían
  inicialización adicional.

Build real: **436 bytes**, relleno con ceros a **512**. SHA-256 rellenado:
`4d336e112ad7a413748667baf1f8bac2ff12acd39b5e8dc23e85e879671ac1e1`.
El compilador es el xPack ARM ya fijado en el proyecto. Se revisó el
desensamblado generado, incluida preservación de magic antes del prólogo.
Esto sigue sin probar niveles eléctricos, temporización ni recuperación real.

```sh
rtk proxy python3 scripts/build_jumploader.py
rtk proxy python3 scripts/build_firmware.py --keymap custom42_fn
rtk proxy python3 -m unittest discover -s tests -v
rtk proxy python3 scripts/check_port_readiness.py
```

No se descargan herramientas ni se accede a USB con estos comandos. El
jumploader y su manifiesto quedan en `build/jumploader/`, excluidos de Git.
La suite completa remota pasa **26 tests**, incluida la inferencia sobre la
imagen local. En una copia pública sin esa imagen, ese test se omite.

## Variante 42 + F1–F12

`custom42` sigue siendo exactamente 42 posiciones. `custom42_fn` conserva
esas posiciones y agrega las doce teclas físicas de función en **todas las
capas**: 54 posiciones activas, cuatro capas, las cinco averiadas desactivadas.
Se compiló realmente: **17316 B**, la misma reserva de RAM de **1960/2048 B**
y **88 B de heap**. No aumenta la matriz ni el número de capas almacenadas.
Son mapas estáticos compilados QMK; en esa fase no ofrecían edición Vial.

## Qué impide instalar todavía y próximo trabajo concreto

Mapa propuesto, **no una orden de escritura**:

| Región | Uso propuesto |
| --- | --- |
| `0x0000–0x01ff` | Jumploader nuevo |
| `0x0200–<0x7800` | Aplicación QMK |
| `>=0x7800` / opciones de chip | Fuera del candidato; no borrar ni desproteger |

**No instalar el jumploader solo sobre el OEM:** éste está enlazado en cero,
no en `0x200`. Tampoco sirve preservar a ciegas los primeros 512 B OEM.
No se generó una imagen combinada ni un instalador que salte controles.

1. Resolver la discrepancia de checksum/interpretación mediante análisis del
   cálculo usado por el actualizador, sin ejecutarlo. Seguir buscando una
   lectura no destructiva o una restauración apropiada, no fuzzear comandos.
2. Evaluar la secuencia de programación de páginas SN32F26x y preservación del
   ISP; la dirección de salto ROM por sí sola no garantiza inmutabilidad.
3. Revisar cómo comprobar el rescate Escape y la matriz sin una primera
   escritura irrecuperable. **No hay todavía una ruta demostrada compatible
   con la carcasa cerrada.** No convertir una autorización general en esa
   evidencia ni pedir abrir el teclado.
4. Solo cuando exista un plan de recuperación técnicamente sustentado, ensayar
   arranque mínimo, teclas, capas y uso máximo de pila. Luego evaluar
   almacenamiento persistente y Vial con los 2 KB reales de RAM.

El comprobador sigue dando **2 / NOT READY TO FLASH**. Entrar y volver del ISP
original es un hito cumplido, no el cumplimiento del objetivo final.
