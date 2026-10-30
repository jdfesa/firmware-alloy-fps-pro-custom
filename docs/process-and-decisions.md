# Cómo se llegó al firmware editable

Esta página explica el razonamiento y enlaza evidencia, sin convertir inferencias
en hechos ni presentar una receta universal. Estado actual: [README](../README.md).

## Criterio de evidencia

- **Observado:** descriptor, respuesta USB, compilación, lectura de mapa o salida
  humana realmente comprobados, siempre con alcance concreto.
- **Inferido:** matriz/pines o candidato MCU deducidos de una imagen de referencia
  y fuentes externas; no equivalen a inspección eléctrica de esta unidad.
- **Simulado:** fallos o cortes de alimentación sobre modelos host; no son
  interrupciones de alimentación sobre el teclado físico.
- **Pendiente:** recuperación OEM, app deliberadamente corrupta, revisión exacta,
  matriz completa, high-water de pilas, desgaste y estabilidad prolongada.

## Hitos y decisiones

| Fase | Qué se hizo y por qué | Conclusión y límite |
| --- | --- | --- |
| Identificación | Etiqueta/modelo y metadata OEM, sin abrir la carcasa. | HX-KB4RD1-US, OEM 0951:16d2/2112; no identifica PCB o encapsulado. |
| Búsqueda de base | Se revisaron SonixQMK y antecedentes; Origins Core es otro modelo. | Usar plataforma SN32F26x como base, no copiar un binario ajeno. |
| Análisis estático | Extraer una imagen de distribución y seguir arranque, USB y tablas de matriz sin ejecutar updater/DLL. | Matriz 14×8 y pines candidatos. Imagen de referencia, no dump ni OEM autenticado. |
| Primer ARM | Compilar con QMK/ChibiOS fijados y xPack GCC. | La app enlaza en 0x200, no en cero; exige un arranque compatible y revisión de rangos. |
| ISP sin flash | Ciclo OEM→ISP, consultas versión/checksum y retorno; escritura humana confirmada. | Familia F260/CS0 observada; aún no recuperaba una aplicación inválida. |
| Rescate mínimo | Jumploader pequeño con Escape antes de QMK. Se aceptó riesgo residual sin esperar una restauración OEM perfecta. | Revisado antes de instalar; no se declaró seguro por aceptación del usuario. |
| Primera instalación | Conjunto arranque+default, ACK/eco, ISP y luego escritura humana; Escape al reconectar. | Hardware arrancó; no readback completo ni garantía contra todos los fallos. |
| Presupuesto USB | Raw HID upstream excedía RAM. Se midieron variantes y se compactaron estructuras sin recortar pilas a ciegas. | Transporte compacto enlaza; caber no prueba estabilidad. |
| Vial de lectura | Identidad, definición y lectura de cuatro capas sin mutación. | GUI reconoció READ-ONLY; detección no significaba edición. |
| Persistencia | Dos bancos físicos por páginas, CRC/readback y commit final; pruebas host de fallos, luego escritura física. | Configuración sin duplicar mapa en RAM; no garantía contra desgaste/brownout que afecte otras páginas. |
| Edición inicial | Q→Z por herramienta acotada, desconexión y salida humana; restauración. | Núcleo persistente demostrado, no todavía GUI. |
| Geometría y Mac | Definición TKL física, transporte ISP macOS, app-only conservando arranque/mapas. | TKL visible y mapa anterior completo preservado. |
| Descubrimiento desktop | La variante heredaba EXPERIMENTAL; el GUI busca la marca pública vial:f64c2b3c. | Corregido descriptor y detección real en Vial desktop. |
| Desbloqueo y GUI | Primero menú Security→Unlock, luego Tab+Caps; editar con clics. | GUI guardó tres E en capa1; lectura completa y Fn+A tras reconexión confirmaron persistencia. |
| Restauración de prueba | Volver a transparentes desde GUI tras otro unlock. | Nuevo cold reconnect: mapa inicial completo y cero diferencias. |

## Errores y confusiones que conviene no repetir

1. Un JSON de distribución no convierte firmware OEM en Vial.
2. Cuatro capas compiladas y una GUI que detecta no prueban configuración editable.
3. La rejilla eléctrica 14×8 no representa visualmente un TKL: se separaron ambas.
4. Compartir MCU no permite compartir binario ni mapa GPIO.
5. `ReadData` de la DLL era recepción GET_FEATURE, no evidencia de un comando de
   volcado de flash. Un checksum de 16 bits tampoco es un backup.
6. Flash libre no es RAM libre; reducir capas estáticas no solucionó el overflow
   del transporte. Pilas reservadas no son high-water medido.
7. El modo de edición bloqueado puede aparentar un fallo de guardado. Tab+Caps
   solo actúa después de iniciar Unlock, y cada reconexión vuelve a bloquear.
8. La GUI puede mostrar optimistamente SET rechazados; verificar lectura y salida
   después de desconectar. No afirmar Q→Z cuando el mapa real mostró tres E.
9. Una entrada de rescate no es restauración OEM ni prueba de invulnerabilidad.

## Dónde están las fuentes

- Identidad, imagen y matriz: [identificación](hardware-identification.md),
  [extracción](closed-case-development.md), `hardware/matrix-inference.json`.
- Offset, vectores y compilación: [ARM](arm-build-and-boot.md),
  `toolchains/build-lock.json` y `firmware/jumploader/`.
- SONiX manual y protocolo F260 con revisiones: [primer ensayo](first-flash-trial.md).
- Memoria/transporte y modelos anteriores: [presupuesto](vial-memory-budget.md),
  [read-only](vial-readonly-prototype.md), [almacén simulado](vial-map-store.md).
- Backend real, formatos y whitelist: [editable](vial-editable.md), fuentes C.
- Descubrimiento desktop: [util.py oficial e42622c](https://github.com/vial-kb/vial-gui/blob/e42622c352b69eff523a467718db487ab9c9cbf2/src/main/python/util.py).
- Transporte Feature: [contrato hidapi](https://libusb.info/hidapi/group__API.html),
  [adaptador Mac](macos-update.md), tests y evidencia saneada.
- Cronología y resultados: [bitácora](project-log.md),
  `hardware/first-flash-evidence.json` y `hardware/validation-status.json`.

Los informes históricos mantienen su fecha y sus límites. No se reescriben como
si todo hubiera estado probado desde el principio; se señalan desde el README.
