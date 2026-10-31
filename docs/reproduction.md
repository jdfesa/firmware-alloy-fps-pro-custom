# Requisitos reales y reconstrucción

> [!WARNING]
> Compilar no autoriza instalar en otra unidad. No hay un flasher universal,
> backup OEM o restauración de fábrica comprobada. Leer primero
> [seguridad y recuperación](safety-and-recovery.md).

## No hacen falta dos equipos ni dos sistemas operativos

El proceso tiene tres tareas independientes. Pueden compartir un equipo con
herramientas/transportes compatibles. Separarlas entre equipos fue una decisión
práctica del ensayo, **no un requisito del teclado**. La configuración diaria
no requiere compilar ni instalar firmware de nuevo.

| Tarea | Requisitos reales |
| --- | --- |
| Configurar el mapa | Firmware compatible ya instalado, Vial, desbloqueo físico y códigos admitidos. Sin compilador C. |
| Reconstruir el candidato | Git, Python, GNU Make, compilador cruzado ARM con binutils y dependencias/revisiones fijadas. No requiere acceso USB. |
| Instalar o actualizar | Candidato revisado y su manifiesto, identidad/protocolo/rangos/arranque sustentados, plan de rescate y transporte USB implementado con permisos adecuados. Es la fase de riesgo. |

## Compatibilidad real de las herramientas actuales

Esta tabla describe implementaciones y pruebas, no exige utilizar las filas juntas.

| Componente | Compatibilidad/estado |
| --- | --- |
| Código C/ASM del teclado | Ejecuta en el controlador Cortex-M0 de la familia candidata; no en el sistema operativo del PC. |
| Cliente Vial | Cliente de configuración; el firmware implementa solo un subconjunto. GUI/persistencia comprobadas con Vial 0.7.5. |
| Compilación preparada | Toolchain xPack 12.3.1-1.2 **Linux x86_64**, QMK/ChibiOS fijados. Un binario de ese toolchain no ejecuta nativamente en otro sistema. |
| Instalador hidraw | Backend Linux, biblioteca estándar Python y acceso al dispositivo correcto. Primera instalación y actualizaciones iniciales probadas. |
| Instalador hidapi | Backend macOS con `--mac`, paquete hidapi local; actualizaciones app-only probadas, no primera instalación en este backend. |
| Otros entornos | No se validó un instalador Windows ni un build ARM nativo en otras plataformas. Haría falta preparar/validar el toolchain y backend correspondientes; no prometer que basta cambiar una ruta. |

La arquitectura no depende de tener ambos sistemas. Un entorno que cubra build
y transporte puede concentrar las tareas; el backend hidraw y el toolchain
preparado corresponden a una misma plataforma. Los entornos exactos del ensayo
quedan abajo como procedencia, no como una lista de máquinas que haya que poseer.

## Fuentes y herramientas necesarias

- Git, Python 3 con `lzma`, GNU Make y herramientas de shell compatibles.
- **xPack arm-none-eabi-gcc 12.3.1-1.2**, con binutils. Es el compilador del
  teclado, distinto del compilador host usado para tests C.
- SonixQMK `62973ee48a976c6f7cc6d4f7b198bd48a2fdfe60`, ChibiOS y submódulos
  exactos, además de fuentes Python de generadores fijadas en
  [`build-lock.json`](../toolchains/build-lock.json).
- Compilador C host para harnesses; ASan/UBSan requieren soporte de ese compilador.
  Los tests host no ejecutan el binario ARM ni validan el USB físico.
- hidapi solamente si se utiliza su backend; hidraw no necesita ese paquete.
- RTK para ejecutar literalmente los comandos documentados. Es un wrapper,
  no parte del firmware ni del protocolo del teclado.
- Acceso HID permitido para la interfaz seleccionada, sin habilitar acceso
  indiscriminado a otros teclados y sin capturar sus entradas.

Los binarios/dependencias no se versionan. **La preparación de un clon limpio aún
no tiene un instalador end-to-end validado.** Hay que provisionar exactamente las
revisiones y verificar hashes; los scripts rechazan herramientas ausentes o
fuentes distintas. No saltar controles para hacer pasar un build. Detalles del
primer entorno preparado: [informe ARM](arm-build-and-boot.md).

## Registro del candidato que realmente se probó

[`reconstruction-record.json`](../toolchains/reconstruction-record.json) conserva:

- Commit de fuentes de firmware y hashes de cada archivo que participó.
- Revisiones/locks de dependencias y hashes del parche y sus preimágenes.
- Compilador y checksum del archivo distribuido de herramientas.
- SHA256 de la app y de la imagen con padding, offset/rango, memoria y pilas.
- Geometría de los bancos, formato actual, límites y afirmaciones NO verificadas.

Es un registro público saneado, **no un permiso de flasheo ni un backup**.
Los hashes identifican el artefacto ensayado; no prueban que cualquier entorno
nuevo vaya a producir bytes idénticos sin completar y validar su preparación.
Los resultados binarios locales siguen siendo necesarios para comparar el build
nuevo contra ese registro y su manifiesto antes de considerar una instalación.

El registro está vinculado al commit indicado, no a cada revisión posterior del
repositorio. Una limpieza de comentarios o metadatos también cambia hashes de
fuentes: no actualizar los hashes históricos para aparentar que corresponden a
un build nuevo. Reconstruir y generar un manifiesto nuevo cuando se requiera
validar un candidato con fuentes modificadas.

## Reproducción sin hardware

En un clon de las fuentes identificadas, con dependencias/toolchain preparados:

```sh
rtk proxy python3 -m unittest discover -s tests -v
rtk proxy python3 scripts/check_port_readiness.py
rtk proxy python3 -B scripts/build_compact_raw.py --keymap vial_editable
rtk proxy python3 scripts/flash_trial.py --keymap vial_editable
```

- Suite completa: 107 tests pasan en el entorno preparado. Una exportación pública
  sin toolchain/material propietario ejecutó 103 tests con 2 omisiones explícitas,
  correctamente. Informar skips y dependencias, no afirmar validación omitida.
- Checklist: salida 2/NOT READY TO FLASH por revisión, matriz completa y OEM
  pendientes. Informa, no escribe ni autoriza instalar.
- Build: produce app/manifiesto privados; valida fuentes/parche, memoria y vectores.
  No acepta un target flash. La app comienza en 0x200, no es imagen para escribir desde cero.
- Último comando: **dry-run**. No abre USB ni programa el teclado.

No regenerar matriz a partir de cualquier imagen ni sustituir archivos ausentes
por firmware de otro modelo. Revisar las fuentes/método en
[proceso y decisiones](process-and-decisions.md).

## Instalación o actualización: condiciones previas

1. Contrastar modelo, descriptor, revisión y familia sin borrar/desproteger.
2. Revisar manual/protocolo y límites del candidato concreto, no deducir rangos
   del tamaño de un archivo. No usar el checksum de otra unidad como autorización.
3. Disponer de rescate independiente de una app funcional, con riesgo residual
   explícito. La primera reescritura de arranque es distinta de una app-only.
4. Revisar fuentes, manifiesto, hash, vectores, rango y dry-run.
5. Solo en una sesión deliberada y técnicamente revisada, usar el backend
   compatible y seleccionar un único dispositivo. Ante error, detener sin retry.
6. Comprobar rescate, arranque, escritura humana, definición y persistencia;
   enumeración o dibujo optimista no bastan como éxito.

[Primer ensayo](first-flash-trial.md) y [transportes USB](usb-update.md) documentan
la experiencia y sus límites. No son una receta para cualquier Alloy.

## Entornos observados en el ensayo, no requisitos conjuntos

- Compilación ARM: Linux x86_64/Arch, Python 3.14.8, xPack ARM 12.3.1-1.2.
  GCC host 16.2.1 se usó para tests, no para generar la app Cortex-M0.
- Actualizaciones/GUI posteriores: equipo Intel con macOS 15.5, Python 3.14.6,
  Apple Clang 17 para tests host y Vial 0.7.5. RTK 0.43.0/0.45.0 según entorno.
- SSH se utilizó por comodidad para trabajar entre copias; no es una función
  necesaria del firmware. No se publican credenciales, cuentas o direcciones.

## Contribuciones

Separar observado/inferido/simulado; probar parsers y límites; medir flash/RAM
sin recortar pilas a ciegas; versionar/migrar almacenamiento antes de cambiar
geometría/capas. No publicar material propietario, fotos de etiqueta o logs crudos.
Conventional Commits en inglés y revisión del índice antes de push. GitHub respalda
fuentes, no OEM. Ver [publicación](publication-review.md).
