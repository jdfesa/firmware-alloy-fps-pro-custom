# Prerrequisitos y reproducción responsable

> [!WARNING]
> Reproducir una compilación no autoriza instalarla en otra unidad. No hay un
> instalador universal, backup OEM ni restauración de fábrica comprobada.
> Leer primero [seguridad y recuperación](safety-and-recovery.md).

## Separar tres actividades

| Actividad | Qué hace falta |
| --- | --- |
| Configurar una unidad ya instalada con este candidato | Vial, desbloqueo físico y asignaciones admitidas. No requiere C ni compilación. |
| Estudiar fuentes, ejecutar tests y compilar | Git, Python, compilador host para tests C, toolchain ARM y dependencias fijadas. No requiere tocar USB. |
| Primera instalación o actualización | Todo lo anterior más evidencia de identidad, protocolo/rangos, arranque, recuperación y acceso exclusivo al HyperX. Es la fase de riesgo. |

## Máquinas usadas en el ensayo documentado

| Papel | Entorno observado al 2026-10-30 |
| --- | --- |
| Fuente principal, HyperX USB, Vial e instalación | Mac Intel x86_64, macOS 15.5, Python 3.14.6, Apple Clang 17, RTK 0.43.0. |
| Build ARM y tests host | Linux x86_64, Arch Linux; Python 3.14.8, GCC host 16.2.1, RTK 0.45.0. |
| Compilador del teclado | **xPack arm-none-eabi-gcc 12.3.1-1.2**, no el GCC/Clang host anterior. |

SSH conectó ambos entornos sin mover el teclado para compilar. No se publican
nombres de cuenta, direcciones, claves o contraseñas de esas máquinas. Estas
versiones describen el ensayo, no afirman que sean las únicas compatibles.
El toolchain importado de Linux no es ejecutable nativo de macOS. Apple Silicon,
Windows y otras revisiones/entornos no se validaron aquí como instaladores.

## Herramientas y dependencias

- Git y utilidades de shell; GNU Make y toolchain ARM con binutils para el build.
- Python 3 con biblioteca estándar, incluido `lzma`; dependencias Python de los
  generadores QMK en las revisiones de `toolchains/build-lock.json`.
- Compilador C **host** para harnesses de tests. ASan/UBSan requieren soporte del
  compilador usado; no ejecutan el firmware ARM ni prueban el USB físico.
- SonixQMK `62973ee48a976c6f7cc6d4f7b198bd48a2fdfe60` y submódulos fijados en el lock;
  no usar automáticamente el último QMK upstream como si fuera equivalente.
- Para USB Mac se usó el paquete hidapi aislado bajo
  `artifacts/tools/macos-hid`; no se instala ni se abre USB al importar el módulo.
- RTK es el wrapper de comandos empleado por el proyecto, no parte del firmware.
- Vial de escritorio o un navegador compatible con WebHID para el cliente web;
  un solo cliente a la vez. Vial desktop observado: **0.7.5**, según Info.plist
  del bundle instalado; las referencias fuente de protocolo se fijan aparte.

Los binarios/dependencias no se incluyen en Git. **La preparación completa de un
entorno limpio todavía no tiene un instalador end-to-end validado.** Hay que
provisionar las revisiones y comprobar hashes del lock; los scripts rechazan
fuentes distintas o herramientas ausentes, no deben saltarse esos controles.
Ver detalles de preparación y primer enlace en [el informe ARM](arm-build-and-boot.md).
No ejecutar el actualizador propietario para preparar el entorno.

## Secuencia sin hardware

Desde la raíz, con herramientas y dependencias ya preparadas:

```sh
rtk proxy python3 -m unittest discover -s tests -v
rtk proxy python3 scripts/check_port_readiness.py
rtk proxy python3 -B scripts/build_compact_raw.py --keymap vial_editable
rtk proxy python3 scripts/flash_trial.py --keymap vial_editable
```

- Tests: 107 ejecutados correctamente en el entorno Mac preparado. Una copia
  pública sin artefactos propietarios o toolchain puede omitir pruebas explícitas;
  informar esos skips, no prometer el mismo número de comprobaciones.
- El checklist devuelve **2 / NOT READY TO FLASH** mientras falten revisión,
  validación de matriz completa y restauración OEM. No escribe ni autoriza USB.
- El build real usa el toolchain Linux, parche con preimágenes comprobadas y
  manifiesto con hashes/memoria. No acepta un target flash.
- El último comando es **dry-run**: valida fuentes/imagen, vectores, padding y
  rango; no abre el teclado ni instala nada.

No regenerar la matriz a partir de cualquier imagen. Los scripts de extracción
solo tienen sentido sobre el material de referencia revisado y no lo convierten
en un backup. Una imagen ausente en un clon público no justifica usar otra a ciegas.

## Antes de escribir en otra unidad

1. Contrastar modelo, descriptor, revisión y familia sin desproteger ni borrar.
2. Revisar el manual/protocolo y los límites de la imagen concreta. No asumir
   inmutabilidad del ISP por conocer una dirección de salto.
3. Tener un plan de rescate independiente de una app funcional, con riesgo
   residual explícito. No copiar el jumploader solo encima del OEM.
4. Comprobar las fuentes y binario contra el manifiesto y revisar el dry-run.
   No reutilizar hashes/checksums de esta unidad como autorización para otra.
5. Solo en una sesión deliberada y técnicamente revisada, seleccionar un único
   dispositivo y alcance. Ante una transferencia inválida, detenerse sin retry.
6. Verificar rescate, arranque, escritura humana, configuración y persistencia;
   no publicar como éxito una simple reenumeración o el dibujo de la GUI.

Los detalles técnicos de la primera instalación están en
[primer ensayo](first-flash-trial.md); las posteriores actualizaciones Mac en
[macOS](macos-update.md). Son evidencia de un proceso acotado, no una recomendación
para flashear sin revisión. Los comandos destructivos no se presentan aquí como
«copiar y pegar para cualquier Alloy».

## Contribuir sin invalidar la evidencia

- Separar observado, inferido y simulado. No cambiar un booleano a true por conveniencia.
- Añadir pruebas por cada cambio de parser, almacenamiento, límite o transporte.
- Medir flash/RAM y no reducir pilas a ciegas para lograr enlazar.
- Versionar/migrar almacenamiento antes de cambiar geometría o cantidad de capas;
  preservar arranque y mapas en actualizaciones ordinarias.
- No versionar material propietario, herramientas, fotos de etiqueta o logs crudos.
- Conventional Commits en inglés y revisión del índice antes del push. GitHub es
  respaldo de fuentes, no dump OEM. Revisar [publicación](publication-review.md).
