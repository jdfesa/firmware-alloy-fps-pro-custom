# Objetivo y reglas de este proyecto

## Antes de continuar

1. Leer [README](README.md), [estado y límites](docs/status-and-limits.md),
   [seguridad](docs/safety-and-recovery.md) y [continuación](docs/next-steps.md).
2. Consultar la [bitácora](docs/project-log.md), `hardware/validation-status.json`
   y la evidencia enlazada antes de afirmar que algo está probado.
3. Los informes de build, USB y planificación son antecedentes fechados, no
   listas de pendientes actuales. No repetir ensayos ya verificados.

## Objetivo y estado de referencia

Crear firmware para el **HyperX Alloy FPS Pro HX-KB4RD1-US**, conservando su
controlador y permitiendo usar unas 42 posiciones con capas de números,
símbolos y navegación. La base es SonixQMK. Un mapa estático de cuatro capas
no equivale a configuración dinámica desde Vial.

Resultados de hardware al **2026-10-30**, sobre una sola unidad:

- `vial_editable` instalado: TKL ANSI de 87 posiciones dibujadas, 82 útiles y
  cuatro capas. `8 9 0 - =` siguen deshabilitadas; dibujarlas no las repara.
- Vial de escritorio detecta el dispositivo. Tras Security → Unlock y Tab+Caps,
  la GUI cambió A/S/D de capa 1 a E; relectura de 896 B, reconexión y Fn+A → E
  confirmaron persistencia. Restauración desde GUI y otra reconexión devolvieron
  el mapa original completo. Q→Z fue un ensayo anterior por herramienta, no GUI.
- Actualizaciones macOS app-only en `[0x200,0x55c0)`, fuera de arranque y bancos.
  F260/CS0, ACK/eco y retorno comprobados; no lectura completa de flash.
- Escape al reconectar alcanzó ISP con Bootmagic de la app deshabilitado.
  No se probó una app deliberadamente corrupta ni restauración OEM.
- App de 21 412 B; RAM reservada 1968/2048 B incluidas pilas. No es Vial-QMK
  completo ni firmware estable. Reconexión general y máximos de pila pendientes.

Detalles: [editable](docs/vial-editable.md), [actualización](docs/usb-update.md)
y `hardware/first-flash-evidence.json`. El estado vigente se mantiene en las
guías enlazadas, no duplicando resúmenes en cada informe histórico.

## Fuente de trabajo y entornos

- Usar la copia de trabajo actual como fuente principal. Antes de sincronizar
  con otra copia, comparar cambios y no sobrescribir diferencias sin revisión.
  El trabajo inicial conservado forma parte del proyecto; no descartarlo.
- README es la entrada única; fuentes, scripts, pruebas y documentos forman un
  solo repositorio. GitHub conserva lo versionado, no artefactos ignorados.
- El entorno ensayado compiló en Linux y configuró/actualizó en macOS. Esto no
  exige dos equipos: ver [compatibilidad por tarea](docs/reproduction.md).
  La compilación remota no requiere mover el teclado ni acceder a su USB.
- Confirmar dónde está conectado el HyperX antes de cualquier diagnóstico;
  no asumir acceso USB por disponer de SSH o de metadatos sysfs.
- Los binarios Linux importados no son ejecutables nativos de macOS.

## Límites obligatorios

- **No abrir, desmontar, soldar ni manipular internamente el HyperX.** Mantener
  la carcasa cerrada y no solicitar fotos internas.
- Seleccionar exclusivamente el HyperX previsto. No consultar, reconfigurar,
  flashear ni capturar entradas de otros dispositivos. Un archivo de referencia
  no concede autorización para acceder al hardware del que procede.
- Teclas averiadas reportadas: `8 9 0 - =`; Backspace funciona. `custom42` no
  utiliza esas posiciones. No prometer repararlas por firmware.
- Una autorización general para experimentar no valida un protocolo, offset o
  procedimiento de recuperación. No escribir un binario a ciegas.
- No quitar protección de lectura para obtener un backup: el MCU candidato
  puede borrar User ROM al desprotegerse. No usar unlock/unprotect/mass erase.
  El Unlock de edición de Vial es distinto y no cambia la protección del MCU.
- No ejecutar el actualizador propietario ni su DLL; solo análisis estático.
- No adivinar rangos a partir del tamaño de archivos o bancos virtuales de tests.
  Conservar arranque, bancos de mapas y región ISP en actualizaciones app-only.
- No sustituir el objetivo por un remapeador del PC o adaptador externo sin
  acordar explícitamente el cambio. Un adaptador no es firmware en el HyperX;
  hardware no identificado no es un programador USB universal.

## Criterio de recuperación e iteración

La primera prueba priorizó una vía mínima para cargar otro candidato aunque
QMK fallara, sin exigir una restauración OEM perfecta como condición absoluta.
Esa decisión y su riesgo residual constan en el [plan histórico](docs/first-trial-planning-history.md).

- Sustentar protocolo, rangos y una entrada de rescate independiente de QMK
  antes de escribir. La primera instalación del arranque también puede fallar;
  no prometer que esta estrategia elimina todo riesgo de bloqueo.
- Si una app falla pero responde el rescate, revisar otro candidato app-only
  conservando el arranque. No reintentar escrituras automáticamente.
- Una distribución funcional equivalente a la de fábrica es una alternativa
  mínima, no restauración OEM ni reparación de las cinco teclas averiadas.
- No exigir circularmente una instalación previa para evaluar un primer ensayo,
  ni declarar comprobada una recuperación por aceptar su riesgo residual.
- La exportación DLL ReadData es recepción GET_FEATURE, no evidencia de dump.
  La imagen de referencia y un checksum no son un backup de la unidad.

## Comandos y evidencias

Todas las órdenes de shell deben comenzar con `rtk`; usar `rtk proxy` si no
existe subcomando específico. Estas reglas no dependen de rutas personales.

```sh
rtk proxy python3 -m unittest discover -s tests -v
rtk proxy python3 scripts/check_port_readiness.py
rtk proxy python3 scripts/build_firmware.py --keymap custom42
rtk proxy python3 scripts/build_firmware.py --keymap default
rtk proxy python3 scripts/build_firmware.py --keymap custom42_fn
rtk proxy python3 scripts/build_jumploader.py
rtk proxy python3 -B scripts/build_compact_raw.py --keymap vial_editable
rtk proxy python3 -B scripts/build_compact_raw.py --keymap vial_readonly
rtk proxy python3 -B scripts/measure_map_store.py
```

El comprobador devuelve **2 / NOT READY TO FLASH** mientras falten evidencias.
Solo informa: no autoriza ni ejecuta escrituras. No cambiar validaciones a
`true` para forzar READY. Los builds requieren dependencias preparadas en
`artifacts/tools`, con revisiones fijadas en `toolchains/build-lock.json`.

El [informe ARM](docs/arm-build-and-boot.md), el [presupuesto Vial](docs/vial-memory-budget.md),
el [prototipo de lectura](docs/vial-readonly-prototype.md) y el [almacén simulado](docs/vial-map-store.md)
conservan medidas de etapas anteriores. Sus bancos virtuales no son direcciones
físicas y sus resultados host no validan desgaste, cortes reales o USB.

## Documentación y publicación

- Redactar documentación autónoma y neutral para cualquier lector, incluido
  quien retome el proyecto más adelante. No depender del chat, pertenencias o
  decisiones personales ni presentar el diálogo de desarrollo como instrucciones.
- Describir requisitos por tarea, capacidades y condiciones reales del ensayo.
  No convertir la organización de equipos de desarrollo en requisito universal.
- Separar guías vigentes, evidencia de la unidad ensayada e historia fechada.
  Conservar modelos, fechas, hashes y límites; no duplicar un «estado actual»
  en informes históricos ni actualizar sus hashes como si fueran builds nuevos.
- Documentar avances significativos en `docs/project-log.md`. Separar observado,
  inferido, simulado y pendiente. No afirmar «estable», «instalado», «recuperable»
  o «backup» sin evidencia concreta y alcance explícito.
- Antes de añadir archivos, leer [publicación](docs/publication-review.md).
  Excluir binarios propietarios, herramientas, fotos de etiquetas, temporales,
  logs y snapshots privados. No registrar números de serie, SP ni códigos de foto.
- Solo cuatro JSON revisados de `artifacts/analysis` están permitidos por
  `.gitignore`; no ampliar esa lista sin revisar contenido y rutas personales.
- Revisar el índice real; Conventional Commits en inglés. No crear remotos ni
  publicar o hacer push sin petición explícita. La licencia está en `LICENSE`;
  la revisión de atribuciones de terceros no se da por completada.
