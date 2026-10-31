# Hitos técnicos del proyecto

Resumen de cambios y resultados que explican la evolución del firmware, no una
guía de instalación. Estado vigente: [capacidades y límites](status-and-limits.md).
Para reconstruir el candidato ensayado, usar [requisitos](reproduction.md) y el
[registro de fuentes y hashes](../toolchains/reconstruction-record.json).

## 2026-10-29 — Identificación y reconstrucción de matriz

- SKU HX-KB4RD1-US y OEM `0951:16d2` / `bcdDevice=2112` documentados sin abrir la
  carcasa. La revisión de PCB y el encapsulado MCU no quedaron verificados.
- Imagen v2112 extraída estáticamente de un espejo de terceros, sin ejecutar
  updater/DLL. No es un dump de la unidad ni una restauración OEM autenticada.
- Matriz 14×8 y 87 códigos primarios inferidos; cinco posiciones averiadas
  excluidas del mapa reducido. Se generaron `default`, `custom42` y `custom42_fn`.
- Evidencia y método: [identificación](hardware-identification.md),
  [extracción y matriz](closed-case-development.md), `hardware/matrix-inference.json`.

## 2026-10-29 — Compilación ARM y contrato de arranque

- QMK/ChibiOS y xPack ARM GCC fijados en `toolchains/build-lock.json`.
  `custom42` y `custom42_fn`: 17 316 B; `default`: 16 868 B.
- La aplicación se enlaza en `0x200`, no en cero. Jumploader C/ASM de 436 B,
  rellenado a 512 B, con Escape previo a QMK y validación de vectores.
- Los candidatos iniciales reservaron 1960/2048 B de RAM incluidas pilas;
  88 B de heap no equivalen a margen de pila medido.
- Consulta OEM→ISP→OEM confirmó familia SN32F26x, CS0 y escritura posterior,
  pero no recuperación ante aplicación fallida. ReadData de la DLL se identificó
  como GET_FEATURE, no como prueba de lectura de flash.
- Fuentes: [ARM y arranque](arm-build-and-boot.md), [protocolo ISP](usb-isp-and-startup.md).

## 2026-10-29 — Transporte compacto y persistencia simulada

- Raw HID upstream excedió 2048 B de RAM: 2392 B, o 2240 B sin tapping.
  El parche compacto permitió enlazar `raw_compact` con 1952 B reservados,
  sin recortar las pilas de 224/480 B. `vial_readonly` añadió protocolo de
  lectura Vial 6 / VIA 9 sin aumentar esa reserva.
- Almacén host de dos bancos virtuales, CRC y commit final: estado de 8 B,
  sin duplicar el mapa de 896 B en RAM; 29.266 escenarios de fallo simulados.
  Esos bancos no eran direcciones físicas ni persistencia probada en hardware.
- Método y mediciones: [presupuesto](vial-memory-budget.md),
  [prototipo de lectura](vial-readonly-prototype.md), [modelo de mapas](vial-map-store.md).

## 2026-10-30 — Primera instalación y configuración editable

- Primera imagen arranque+`default`: `[0,0x4400)`, 272 reportes. ACK/eco,
  arranque QMK y escritura humana comprobados; no readback completo de flash.
- `vial_readonly` confirmó descubrimiento y lectura, sin edición. El backend
  editable posterior usó páginas de 64 B y dos bancos físicos en `0x7000..0x7800`,
  separados de arranque e ISP. Se probaron 52.275 cortes simulados, no reales.
- Edición Q→Z por herramienta, reconexión, salida física y restauración
  comprobaron persistencia de una tecla; ese ensayo no fue una edición GUI.
- Evidencia: [primer ensayo](first-flash-trial.md), [editable](vial-editable.md)
  y `hardware/first-flash-evidence.json`.

## 2026-10-30 — TKL, Vial desktop y restauración desde GUI

- Geometría física separada de la matriz eléctrica. El gráfico final muestra
  87 posiciones y mantiene 82 utilizables; las cinco averiadas siguen `KC_NO`.
- Actualizaciones macOS app-only en `[0x200,0x55c0)` preservaron arranque y mapa.
  Escape alcanzó ISP con Bootmagic de app deshabilitado, aislando el jumploader.
- La marca pública `vial:f64c2b3c` corrigió el descubrimiento desktop.
  Security → Unlock antes de Tab+Caps permitió editar desde la GUI.
- A/S/D de capa 1 pasaron a E; mapa completo idéntico tras reconectar y salida
  Fn+A→E confirmada. Otro desbloqueo permitió restaurarlas a transparentes;
  una nueva reconexión recuperó los 896 B originales y el estado bloqueado.
- Candidato final: app de 21 412 B, RAM reservada 1968/2048 B, definición XZ de
  416 B; 107 tests host pasaron. Timeouts generales, máximos de pila, desgaste,
  estabilidad prolongada y recuperación OEM siguen sin validación completa.
- Detalles: [editable](vial-editable.md), [transporte](usb-update.md),
  [reconstrucción](reproduction.md) y [evidencia](../hardware/first-flash-evidence.json).

## 2026-10-31 — Claridad documental

- Guías separadas de informes históricos; eliminados resúmenes de estado
  duplicados y aclaradas geometría vigente y duración de desbloqueo en la GUI.
- README español/inglés y política de publicación reconocen LICENSE, añadido
  en `e8f2b53`; la revisión de atribuciones de terceros sigue pendiente.
- Comentarios y metadatos descriptivos neutralizados sin cambiar keycodes,
  tiempos, mapas, rangos o indicadores de validación. Los hashes del candidato
  ensayado permanecen vinculados a su commit, no a esta revisión documental.
- Verificación sin hardware: 107 tests pasan; enlaces locales revisados.
