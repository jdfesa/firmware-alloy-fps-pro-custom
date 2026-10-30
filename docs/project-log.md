# Bitácora del proyecto

## 2026-10-29 — Análisis inicial

- Objetivo: reaprovechar únicamente el HyperX Alloy FPS Pro con capas y unas 42 teclas activas. No intervenir el Silakka54.
- Identidad USB observada: `0951:16d2`, producto Kingston HyperX Alloy FPS Pro; `bcdDevice=2112`.
- Investigación pública: MCU Sonix SN32F268FG documentado en un desmontaje de otra unidad; soporte de familia en SonixQMK, pero sin port FPS Pro listo identificado en la búsqueda acotada.
- Se encontró un antecedente comunitario de fallo de las mismas cinco teclas por una pista interrumpida. No se diagnosticó la unidad del usuario.
- Se creó el informe de viabilidad en [README.md](../README.md).
- Sin pulsaciones capturadas, comandos HID/USB, flasheos, instalaciones o remapeadores activados. Solo metadatos sysfs y fuentes públicas.

## 2026-10-29 — Etiqueta y estrategia de respaldo

### Hecho

- Recibida foto inferior del HyperX. Confirmados SKU `HX-KB4RD1-US`, referencia `3500241-001.A02LF`, nominal `5 V CC / 500 mA`.
- Registrada la [identificación](hardware-identification.md) sin copiar foto original, números de serie, SP ni código matricial.
- El usuario pide documentar el avance en este proyecto y propone priorizar backup antes del port.
- Creado el [plan de respaldo y recuperación](backup-and-recovery.md), con separación entre identificación, paquete oficial y volcado de la unidad.
- Verificada en documentación primaria del MCU candidato la advertencia: desactivar protección de lectura causa borrado masivo de User ROM.
- Revisada documentación de SonixFlasherC: anuncia info/checksum y flasheo, no un comando de volcado completo. No se ejecutó la herramienta.
- Encontrada referencia de soporte HyperX a un actualizador oficial; descarga/validación no realizadas. El enlace corto no fue recuperable en estas consultas y el entorno local no resolvió su dominio.
- Documentados criterios de reutilización: plataforma MCU y matriz real antes que semejanza de distribución o cantidad de teclas.

### Estado al cierre de esta etapa

| Área | Estado |
| --- | --- |
| Modelo exterior | Confirmado por foto y consistente con USB |
| Distribución superior y revisión PCB | Pendientes |
| MCU de esta unidad / protección | No confirmados |
| Paquete original / imagen extraída | No obtenidos |
| Volcado del teclado | No realizado |
| Recuperación / restauración | No validadas |
| Port QMK / Vial | Sin implementar ni flashear |
| Silakka54 | Sin intervención ni acceso a configuración |

### Próxima evidencia propuesta entonces (histórica, sustituida abajo)

Foto superior y, si el usuario acepta abrir **solo el HyperX desconectado**, fotos de PCB, MCU y revisión. Con eso se puede escoger una base de código y estudiar respaldo/recuperación sin adivinar el hardware.

## 2026-10-29 — Desarrollo sin desmontaje

- El usuario rechaza abrir el HyperX y autoriza desarrollar con cuidado. No volver a pedir fotos internas. Silakka54 sigue excluido.
- Paquete v2112 adquirido de espejo comunitario `IRus/blog`; hash y procedencia fijados, autenticidad del fabricante pendiente. Extracción estática por recurso PE/zlib; updater y DLL nunca ejecutados.
- Reconstruidas de la imagen una matriz 14 × 8, 87 códigos primarios y pines candidatos. Descriptor del archivo coincide con el USB observado. Inferencia, no prueba de identidad de PCB.
- Creadas fuentes QMK experimentales `default` y `custom42` con cuatro capas, scripts de extracción/generación y verificación de estado. Se deshabilitan persistencia e iluminación al inicio.
- Pasan 14 pruebas locales, incluida compilación/verificación de tablas C en anfitrión. **No hay build QMK/ARM, flasheo ni prueba funcional en teclado.**
- El análisis REA/Ghidra no está disponible por falta de motor configurado; se continuó con Capstone compilado localmente, sin cambios globales.
- Los binarios de terceros y herramientas locales quedan fuera del versionado mediante `.gitignore`. El HEX no incluye bootloader; el binario rellenado es solo de análisis, no backup ni imagen flasheable.
- Estado detallado, evidencia y próximos pasos: [closed-case-development.md](closed-case-development.md). Recuperación, bootloader y presupuesto real de memoria siguen pendientes; `check_port_readiness.py` devuelve 2.

## 2026-10-29 — Primeros candidatos ARM compilados

- Preparados SonixQMK, ChibiOS, LUFA/printf, fuentes Python y GNU Arm GCC 12.3.1-1.2 dentro de `artifacts/tools`, sin instalación global. Revisiones y checksum en `toolchains/build-lock.json`.
- PyPI no resolvió por DNS; se usaron dependencias de repositorios primarios con commits fijados. El cargador `scripts/qmk_build_cli.py` usa los generadores y esquemas reales de upstream y solo registra comandos de build; no configura otros teclados ni ofrece flasheo.
- Corregida la opción inválida `VIAL_ENABLE=no` de la fuente inicial; Vial no está integrado. Se mantiene VIA deshabilitado, EEPROM transitorio e iluminación desactivada.
- Compilados y enlazados realmente para Cortex-M0: `custom42` **17316 B**, `default` **16868 B**, dentro de los 30208 B de aplicación de la plataforma. Artefactos locales en `build/`, manifiestos y logs en `artifacts/analysis/`.
- Ambos reservan 1960 de 2048 B de RAM hasta el heap: datos 280 B, BSS 972 B, pilas IRQ/proceso 224/480 B y alineación. Quedan 88 B de heap; no es una medida de margen de pila ni estabilidad en ejecución.
- Descubierto en el linker fijado: vectores/aplicación en **`0x200`**, con dependencia del **jumploader** de SonixQMK. La imagen OEM inicia en cero. No se construyó imagen combinada ni se validó o instaló ese arranque auxiliar.
- Añadido Bootmagic con Escape físico al encender. Solo ayuda si arranca la aplicación y funciona su matriz; no garantiza recuperación de un fallo de arranque.
- `scripts/build_firmware.py` limita los mapas permitidos, comprueba revisiones y mapa de memoria y guarda hashes. No abre dispositivos ni escribe firmware.
- **17 pruebas pasan**. La lista de evidencia aún devuelve **2 / NOT READY TO FLASH**, con revisión, matriz, bootloader, recuperación y jumploader pendientes.
- El entorno no expone `/dev/bus/usb`, `/dev/hidraw*` ni `/dev/input`; no se pudo hacer prueba física. No se enviaron comandos a teclados ni se alteró el Silakka54.
- Informe actual: [arm-build-and-boot.md](arm-build-and-boot.md). Próximo hito: validar arranque y recuperación cerrados, y disponer de acceso USB autorizado antes de plantear una escritura.

## 2026-10-29 — Guía de continuación y límites permanentes

- El usuario pide confirmar avances y explicar el arranque auxiliar en términos sencillos. Se aclara que es un pequeño programa en el controlador, no hardware que haya que instalar abriendo el teclado.
- Creado [AGENTS.md](../AGENTS.md) con objetivo, límites, resultados comprobados, comandos y condiciones de seguridad para futuras sesiones. Mantener cerrada la carcasa y excluir el Silakka54 sigue siendo obligatorio.
- Creada [la guía de continuación](next-steps.md), con hitos ordenados, evidencias necesarias, limitación de USB y diferencia entre firmware construido, instalado y estable.
- El usuario menciona tener una ESP32, sin indicar variante. Se consultó documentación primaria Espressif: se documenta como posibilidad de adaptador externo dependiente del modelo, no como programador universal ni solución QMK/Vial ya disponible. No se conectó ni programó.
- Se mantienen los resultados: candidatos ARM `custom42`/`default`, 17 pruebas locales, sin flasheo, sin backup propio y sin prueba funcional del HyperX. Próximo trabajo técnico: análisis de jumploader y recuperación por USB con carcasa cerrada.

## 2026-10-29 — Preparación para publicación pública

- El usuario quiere un repositorio público. Se revisaron los candidatos locales, sin subir archivos ni crear un remoto.
- Retirada una referencia de ruta personal de `AGENTS.md`; ampliado `.gitignore` para excluir locks del editor, informes con rutas locales, desensamblado propietario, fotos y configuraciones locales. Se conservan solo cuatro JSON de evidencia revisados dentro de `artifacts/analysis`.
- Verificada selección mediante Git aislado en un directorio transitorio, sin modificar el `.git` del proyecto: 11 casos de exclusión pasan y no se detectan patrones sensibles revisados entre los candidatos públicos. No equivale a auditar historial: `git status` no pudo operar sobre este proyecto en la sesión.
- Creada [la revisión de publicación](publication-review.md), con límites de la auditoría, comprobaciones previas al push y licencia aún pendiente.
- Propuesto `hyperx-alloy-fps-pro-qmk` como nombre público. No se renombró la carpeta ni se publicó nada.

## 2026-10-29 — SSH, primer ciclo ISP y arranque propio

- Confirmado acceso USB por SSH; selección exclusiva del HyperX/interfaz0.
- Implementado diagnóstico allowlist sin borrar/programar/desproteger. Entrada
  ISP, ACK de versión/checksum, retorno OEM y confirmación humana de escritura.
  Familia SN32F26x, CS0, checksum0x27d1. Datos saneados en hardware/usb-isp-evidence.json.
- Corregida espera de reenumeración (1s insuficiente) con timeout y tests.
- Referencia sum16 0..0x7800=0xc08c no coincide; dominio ISP pendiente. No backup.
- SnxISP_ReadData analizado estáticamente: recibe GET_FEATURE, no demuestra dump.
- Jumploader C/ASM propio436 B, app0x200, Escape inferidoC0/A0, magicDEADBEEF,
  pila debajo del magic, validación SP/PC y límites linker. No instalado.
- Variante custom42_fn compilada17316 B,42+12 teclas/cuatro capas; mismas pilas
  y RAM. Endurecida validación de vectores del build.26 tests remotos pasan.
- Sin flashear, sin Vial, sin cambiar Silakka54. Recuperación ante app inválida
  y restauración original siguen pendientes; checklist permaneceNOT READY.
- Documentación actual en docs/usb-isp-and-startup.md. No Git/push: la carpeta
  remota sigue sin repositorio Git visible. Builds y fuentes externas ignorados.

## 2026-10-29 — Consolidación del proyecto

- Reunidos trabajo SSH y avances nuevos en una única raíz local elegida por el
  usuario. Reconfirmadas37 fuentes/documentos idénticos antes de editar.
- Conservados builds, evidencias y dependencias; importación completa ya
  comprobada por checksum sin diferencias de contenido. La antigua carpeta
  temporal es solo un enlace, no otra copia.
- Documentada fuente única en README/AGENTS. Remoto para buildLinux y hardware;
  futura sincronización por GitHub, sin publicación todavía.

## 2026-10-29 — Presupuesto Vial reproducido

- Git local inicializado en main, sin commits, remoto ni publicación.
- Iluminación ya excluida. Raw HID con colas mínimas excede RAM:2392/2048 B;
  sin tapping/oneshot y serial constante2240/2048 B. No bajar pilas a ciegas.
- Añadido scripts/measure_raw_hid.py y4 tests,30 totales pasan. Ejecutado en
  Linux remoto: reproduce ambos errores de enlace. No es firmware Vial.
- Usuario acepta evaluar3 capas. No se cambió el mapa: las capas estáticas
  están en flash; el ahorro del mapa dinámico futuro no elimina el exceso
  del transporte actual.
- Inspeccionadas fuentes oficiales Vial/GUI fijadas; no se integró protocolo.
- Informe docs/vial-memory-budget.md y revisión de publicación actualizados.
- Sin comandos USB, sin flasheo, sin tocar Silakka54 en esta etapa.

## 2026-10-29 — Continuación remota y prototipo de lectura Vial

- Usuario pide priorizar código en la copia macOS más actualizada por SSH;
  aclara que el HyperX está en Linux local. No se movió ni accedió al teclado.
  Se trabajó con una instantánea temporal para compilar en Linux reutilizando
  el toolchain existente; fuente principal remota, cambios enviados verificando
  hashes previos para no pisar trabajo concurrente. No se sobrescribió el árbol
  de fuentes local anterior ni se reinstalaron dependencias.
- Encontrado avance preexistente aún no reflejado en docs: parche USB compacto,
  runner con preimágenes y39 tests. Raw HID ya enlazaba18536 B/1952 B RAM;
  no atribuir este recorte al nuevo módulo de protocolo.
- Implementado `vial_readonly`: parser C acotado Vial6/VIA9, identidad, definición
  XZ generada,54 posiciones y lectura del mapa896 B en cuatro capas. Adaptador
  QMK usa el mismo `custom42_fn`; no añade un mapa RAM ni reduce pilas/tapping.
- Todos los comandos de escritura/unlock/ISP y lectura de switches se rechazan.
  READ-ONLY visible en USB/definición: GUI revisada puede mostrar un cambio aun
  si SET_KEYCODE se rechaza. No hay configuración ni persistencia falsas.
- Extendido `build_compact_raw.py` con whitelist de dos mapas, control de
  definición generada y manifiestos de alcance explícito. Lock independiente
  de referencias Vial; upstream se mantiene limpio tras aplicar/restaurar parche.
- Nuevo build real ARM19460 B, RAM1952/2048 B, heap96 B, IRQ224/proceso480;
  `.data`388 B y`.bss`852 B. No máximo de pila medido ni detección física.
- Recompilado `raw_compact` como control de regresión:18536 B y exactamente
  el mismo SHA-256 anterior530f7278aa5862cfbd3299b610632ae05fe8d28bd068a768246cac694efa8824.
  Confirmado READ-ONLY en el descriptor USB compilado del prototipo nuevo.
- Once tests nuevos:50 totales pasan en Linux y macOS; parser/adaptador C real,
  consultas de descubrimiento simuladas, límites/offsets/paginación y sanitizers
  con65.536 combinaciones. Corregido MO del antiguo shim de tests0x5200→0x5220
  y añadidas aserciones de los dos selectores de capa; el firmware no cambió.
- Checklist sigue2/NOT READY TO FLASH. No USB/flash, no Silakka54, no publicación.
  Detalle y siguiente código: [prototipo de lectura Vial](vial-readonly-prototype.md).

## 2026-10-29 — Comparación de copias y almacén transaccional simulado

- Aclarada la ubicación actual: macOS local como fuente principal; Linux remoto
  por SSH para toolchain y HyperX. Sin contraseñas/direcciones privadas en Git.
- Comparación por SHA-256 sin herramientas descargadas/cachés:91 archivos
  iguales,8 diferentes revisados (todos contienen avances locales),22 solo en
  macOS y2 logs solo en Linux. No faltaban fuentes remotas. Se preservaron
  versiones anteriores en artefactos ignorados y se consolidó sin borrados,
  verificando preimágenes para no pisar cambios concurrentes.
- No se repitió el prototipo de lectura ni el parche USB. Nuevo almacén C de
  mapas: dos bancos virtuales, copia por palabras, CRC, formato versionado,
  commit final, validación de keycodes y fallback. Estado8 B, sin mapa RAM.
- 12 tests nuevos; **62 pasan en macOS y Linux**.29.266 escenarios de cortes y
  errores simulados, además de ASan/UBSan, rollover, corrupción, reintentos,
  offsets impares y política de posiciones. No son cortes sobre el teclado.
- Objeto independiente Cortex-M0 compilado con el GCC fijado:1272 B de código,
  sin `.data`/`.bss`; frame de edición64 B más llamadas. No enlace QMK nuevo ni
  máximo de pila real. No se repitieron builds de candidatos sin cambios.
- Los bancos1024 B son una abstracción, no geometría comprobada. No hay backend
  físico, adaptación de escritura Vial ni firmware editable. Se documentan
  atomicidad por paquete, coste de230 operaciones y desgaste/latencia pendientes.
- Git inicial sin historia; remoto elegido por el usuario sin referencias al
  consultar. Primer commit conserva la base previa; siguiente commit separa
  el almacén nuevo. Mensajes Conventional Commits en inglés y correo noreply.
  Revisión de selección pública sin ampliar los cuatro JSON permitidos.
- Sin USB, flash, desbloqueo de protección ni intervención del Silakka54.
  Checklist sigue2/NOT READY TO FLASH. Siguiente trabajo técnico y límites en
  [vial-map-store.md](vial-map-store.md).

## 2026-10-30 — Prioridad explícita: recuperación mínima y primer ensayo

- El usuario pide no demorar la primera prueba buscando una restauración
  perfecta: priorizar una vía mínima de reprogramación independiente de QMK
  para poder ensayar otro candidato si el primero no arranca.
- Acepta como alternativa un firmware funcional con mapa equivalente al de
  fábrica si no se logra Vial. Se aclara que eso no restaura el OEM por sí solo,
  no funciona sin una aplicación arrancable y no repara posiciones averiadas.
- Revisión acotada del jumploader existente y referencia SonixQMK: se conserva
  la ruta propuesta Escape→ISP antes de QMK. No se implementa otro cargador.
  C0/A0 y funcionamiento real pendientes; vectores válidos no prueban que la
  app no se cuelgue. La entrada de rescate debe cubrir también ese caso.
- Registrado el criterio en AGENTS/README/guías: revisar protocolo, borrado,
  preservación y conjunto arranque+app; ensayar rescate primero, después mapa.
  No exigir circularmente una instalación previa para autorizar el primer
  ensayo, pero explicar su riesgo residual y no afirmar validación anticipada.
- No se alteró ningún indicador de evidencia ni el checklist general. Sin
  cambios de firmware, builds repetidos, comandos USB ni flasheo en este paso.

## 2026-10-30 — Instalador acotado para la primera prueba

- Reconfirmados69 archivos versionados idénticos entre fuente macOS por SSH y
  Linux con HyperX; árboles inicialmente limpios en616519c. Fuentes nuevas se
  escriben en macOS; Linux reutiliza toolchain y USB, sin mover el teclado.
- Revisado manual SONiX v1.9 p.122: User ROM0..0x7800, ISP0x7800..0x8000,
  páginas64B. SonixFlasherC73f9fab8 omite erase explícito paraF260; protocolo
  CMD5=offsetbytes/reportes64B. No se ejecutó updater ni flasher upstream.
- Nuevo flash_trial.py: dry-run por defecto, hashes y vectores, límites,
  HyperX/interfaz0/puerto explícito, F260/CS0/checksum previo, sin erase/security,
  sin reintentos ni reboot automático. Primer conjunto jumploader+default;
  iteraciones soloapp0x200. ACK/eco no se presentan como readback.
- Pruebas de límites, streams, abortos y procedencia; corregida resolución de
  /var frente a /private/var en macOS al comprobar rutas de fuentes de tests.
- Recompilación para seleccionar candidato concreto: default16868B, hash
  646be183c794dc3042c3e1589562f42701d1ae9ccd71e9d8547434ed232b95af;
  jumploader436B/512, mismo hash4d336e11 previo. RAM1960/2048, no runtime aún.
- Plan, fuentes y límites: [primer ensayo](first-flash-trial.md). Ninguna
  evidencia de hardware se cambia antes de observar el resultado.

## 2026-10-30 — Primer flasheo real y arranque USB de QMK

- Ejecutado el instalador revisado con imagen17408B,offset0,272reports y
  consentimiento del usuario, quien mantuvo Escape. Sin erase explícito,
  cambios de seguridad, updater propietario ni intervención del Silakka54.
- ACK y eco finalcorrectos; checksumISP cambió0x27d1→0x1ad2. No readback ni
  dominiochecksum demostrado. Los datos públicos incluyen esta limitación.
- Escape+RETURN_USER llevó a0c45:7010; ISP respondióF260/CS0/checksum.
  Tras soltarEscape, RETURN_USER llevó aQMK FEED:A11F/bcd0001.
- No afirmar estabilidad/matriz completa/Vial editable a partir deenumeración.
  Confirmación humana y prueba de reconexión física todavía pendientes.
- 73tests pasan enLinux/macOS. Commit fuente f3adf1a creado enmacOS y enviado
  aorigin/main mediante el Linuxautenticado (credencialmacOS inválida),
  importando el commit exacto porbundle, sin transferir credenciales.

## 2026-10-30 — Vial real detectado y candidato editable

- Usuario escribió `hola qmk` con default. Cold plug con Escape volvió a ISP.
- App-only vial_readonly instalada sin reescribir arranque:305reportes,checksum
  0x13bd. Consultas RAW reales:VIA9/Vial6,definición336B ymapa896B/cuatrocapas.
  Usuario confirma HyperX READ-ONLY en vial.rocks. No inferir edición de esto.
- Añadido probe_vial.py con selección exclusiva de RAW del HyperX y comandos
  de lectura; no matriz de switches, ni comandos arbitrarios, ni Silakka54.
- El usuario reportó Enter yotrasteclas ausentes: custom42_fn las marcabaKC_NO.
  Se eligió baseinglesa82posiciones excluyendo las5averiadas para elnuevoeditable.
  Usuario aclaró que54uotranúmero sirve; editar ypersistir aldesconectar manda.
- Nuevo vial_editable: snapshots porpáginas64B en0x7000..0x7800,commit separado,
  CRC+readback,lockfísico Tab+Caps,SET_KEYCODE/SET_BUFFER ylectura por escaneo.
  Reserva linker/build/instalador; sinBootmagic deapp para aislar rescatejumploader.
  No seadaptó directamente el modelo4B/FF: manual describe erase0 ypáginas64B.
- 83tests pasan enmacOS;52.275 cortes simulados yASan/UBSan. No son cortes
  reales ni certificación de desgaste. Compilación ARM:21372B antes delcambio
  deUIDdevariante,1968/2048B reservados,80Bheap, pilas224/480sinrecortar.
- Documento deoperación/riesgos: docs/vial-editable.md. Todavía no seha instalado
  este candidato ni probado edición/persistencia alregistrar esteapartado.

## 2026-10-30 — Reanudación en Mac y primera edición persistente real

- Leídas instrucciones/captura privadas aportadas por el usuario; exclusiones privadas comprobadas.
  HyperX movido por el usuario aMac; Linux ahora se reserva para compilar.
- Confirmado candidato editable previamente instalado, contradiciendo el estado
  antiguo de README/AGENTS. No se descartaron los cambios de evidencia existentes.
- Transporte hidapi local aislado, selección única de RAW FEED:A11F/FF60:61.
  No se abre colección bootkeyboard ni se captura matriz/entradas. Timeout inicial
  desapareció con clientes cerrados y reconexión; causa aún no aislada.
- Prueba física completada con el usuario: Tab+Caps, Q→Z, ACK269ms y mapa completo
  coincidente salvoQ; cold reconnect, salida`z` y mismo hashRAW. RestauraciónQ,
  ACK266ms, segundo cold reconnect, salida`q` y hashoriginal. Relock comprobado.
- Se registra persistencia de **una tecla por protocoloVial**, no edición GUI
  ni estabilidad general. No reflasheo deapp/arranque, eraseISP ni desprotección.
- Hallado desajuste deoperación: firmware exige unlock para todoSET, mientras
  GUI solo lopide automáticamente paraRESET. Se documenta desbloqueo explícito.
- Nuevo generador TKL82/seisfilas con espacios para5averiadas, tests degeometría
  y comprobación determinista antes debuild. No cambia matriz/UID/mapa almacenado.
- FuenteSilakka pública leída voluntariamente: cuatrocapas útiles, one-shot y
  multimedia presentes pero no admitidos por subconjuntoactual; no acceso físico.
- Comparación de fuentesLinux:60idénticas,5diferencias revisadas,ningún archivo
  exclusivo remoto. Se prepara buildaislado, sin sobrescribir su árbol previo.
- Build real TKL completado enLinux aislado:21412B app,1968/2048B RAM,80Bheap;
  app-only21440B/335reportes en0x200..0x55c0. Artefactos traídos aMac y hashes
  de todas las fuentes delmanifest cotejados. Candidatoanterior conservado en
  build/trial/installed-editable-before-tkl. **No seinstaló la mejoraTKL.**
- Suite local ampliada:96tests pasan. Falta adaptar/verificar transporteISP
  Mac antes deactualizar, y probar ediciónGUI real con geometría física.

## 2026-10-30 — Actualización TKL real desde macOS por SSH

- Revisión de la fuenteMac b91224f y del material privado aportado sin sobrescribir avances.
  Linux previo conservado; revisión aislada y subidas con hashes depreimagen.
- AdaptadorISP hidapi FeatureReport separado deRAW; ID0+64B enambos sentidos,
  selección única ISP/ruta vigente, app-only0x200..0x7000, sin erase/security,
  OEMentry, reintentos ni reboot automático. Nueve tests nuevos;105 pasan enMac.
- Clientes cerrados y reconexión sinEscape restituyeronRAW; causa del timeout
  no aislada. Snapshot privado de896B antes deactualizar, no backupOEM.
- Usuario reconectó conEscape: ISP respondióF260/CS0 conBootmagic deapp
  deshabilitado. Se indicó soltarEscape antes deactualizar; rescate deapp
  deliberadamente corrupta sigue sin probarse.
- CandidatoTKL preexistente21412B/padded21440B,335reports, SHAimagen
  dd1f768f21b7352eb88b43d881ccba3f23b949cd081e190d188457210d647393,
  escrito una sola vez en[0x200,0x55c0). Checksum0xeb27→0x9ac7;ACK/eco válidos,
  no readbackflash ni dominio checksum demostrado. Sin reescribirjumploader,
  bancos demapas oISP; sin updaterpropietario ni Silakka54.
- RETURN_USER explícito: nueva definiciónANSI TKL416B yhashc9767f77… confirmados.
  Relectura completa896B idéntica al mapa previo, hash94944d6c… .GUI pendiente.

- Usuario confirmó TKL completo enGUI web salvo las5averiadas, pero reporta
  edición aún no disponible y ausencia enappdesktop. Se solicita captura
  conQ seleccionada y confirmación deunlock; no dar tareaGUI por terminada.

- Hallado defecto concreto de descubrimiento desktop: `raw_compact` fija
  SERIAL_NUMBER aEXPERIMENTAL, mientras VialGUIe42622c `find_vial_devices`
  filtra por la marca pública `vial:f64c2b3c` (oVIAregistrado/sideload).
  Corregido solo elconfigeditable y añadida regresión. Nuevo buildARM21412B,
  RAM1968B, mismoTKL/UID/mapas; markerUTF16 comprobado enbinario.106tests pasan
  enMac. Candidato subido con preimágenes ybuildprevio preservado; aúnnoinstalado.
- Aclaración deoperación: Tab+Caps por sísolo no abre nada. Primero elcliente
  debe detectar, luego iniciarSecurity→Unlock y recién mantener lasteclas
  hasta completar labarra (elGUIoficial consulta cada200ms: unos4s).

- Segunda actualización app-only para descubrimiento desktop instalada en el
  mismo rango[0x200,0x55c0):335reports,ACK/eco válidos,checksum0x9ac7→0x53cd,
  retorno ymarcaUSB confirmados. Primer read_map terminó, pero inspectposterior
  agotó timeoutRAW antes delacomparación/registro. No repetir escrituras; se
  pidiócoldreconnect sinEscape y soloappdesktop. Causa deRAW noaislada y
  relecturacompleta deestasegundaactualización todavía pendiente.

- Usuario confirmó detección enVialdesktop tras coldreconnect conmarca corregida.
  Edición aúnpendiente; se guía menúSecurity→Unlock antes deTab+Caps, sin
  nuevosflasheos ni atribuir el sonido reportado auna causa nocomprobada.

- EdiciónGUI real comprobada trasUnlock explícito: A/S/D decapa1 pasaron de
  transparente0x0001 aE0x0008; no ocurrió elQ→Z propuesto. Se comunicó ladiferencia
  sin falsearprueba ni sobrescribir cambios. Mapa896B hash43bd8521… idéntico
  antes/después decoldreconnect, relock yFn+A→E confirmado porelusuario.
- Usuario pidió restaurar esas3posiciones atransparentes. Se guióGUI; comprobación
  final pendiente. Cambios ordinarios ya persisten sinC/recompilación; se mantienen
  límites dekeycodes/funciones y condiciónexperimental, sin estabilidaddeclarada.

## 2026-10-30 — Cierre GUI, restauración y documentación pública

- El aparente fallo al restaurar las tres E era editar después de reconectar
  sin volver a desbloquear. Usuario repitió Security→Unlock y restauró desde GUI.
  Tras cerrar/reconectar, lectura completa896B igual a la base94944d6c…,
  cero diferencias y relock. No se escribieron mapas desde scripts en esta prueba.
- README reorganizado como entrada pública con WARNING de responsabilidad,
  ausencia de backup/restauración OEM, rescate no garantizado, alcance de una unidad,
  modelo exacto y proceso Unlock destacado. No se ofrece receta universal de flash.
- Guías de uso, seguridad, reproducción, proceso/decisiones y límites; firmware
  README actualizado. Informes anteriores conservados y marcados históricos,
  evaluación/plan anterior preservados, sin borrar fuentes ni evidencias.
- Entornos reales documentados: Mac Intel/macOS15.5/Clang17/Python3.14.6,
  Linuxx86_64/Arch/GCC16.2.1/Python3.14.8; compiladorARM xPack12.3.1-1.2.
  No se publican credenciales, direcciones ni rutas personales. No hay provisionado
  limpio end-to-end validado ni licencia global/atribuciones ya resueltas.
- Usuario pidió Conventional Commits en inglés y push desde Mac al remoto existente;
  sincronización Linux solo después de preservar y comparar sus cambios previos.

## 2026-10-30 — Gráfico completo solicitado, sin habilitar posiciones averiadas

- Usuario pidió dibujar87posiciones por estética. Se retiró la omisión del
  generadorKLE; matriz, mapa, UID ywhitelist permanecen iguales. Las5 averiadas
  siguenKC_NO; testC recorre5posiciones×4capas ycomprueba rechazo sinmutaciones.
- App21412B/1968BRAM, XZ416B;107tests pasan enMac. Candidatoanterior conservado.
  Nueva imagenSHAd251bb70ded32c1434488556ec8e4a4ef01ab674520e12a4111ab2bc40a582a0,
 335reports app-only[0x200,0x55c0),checksum0x828d→0x316d,ACK/eco yretorno válidos.
- LecturaUSB: definiciónhashfd6c0f67… con87coordenadas únicas;896B demapa iguales
  aloriginal94944d6c… y5averiadas en0 entodaslas capas. Sin reescribirarranque,
  bancos, seguridad ni usar updater. CapturaGUI ofrecida por usuario pendiente.
- README distingue conectar normal, UnlockTabCaps paraeditar yEscape alconectar
  paraISP/rescate. Origen documentado:5teclas fallaron yse quiso reutilizar resto,
  no reparaciónporfirmware ni causa física diagnosticada.

- Vialdesktop0.7.5 presentó arranque sinresponder/error de comunicación después
  del cambio visual. Se atendió pedido de reiniciar soloapp porSSH, sinfirmware
  niUSB paralelo; usuario informó que luego cargó. Captura privada muestra
  RuntimeError failed to communicate with the device enreload_via_protocol,
  antes dedescargar definición. No se atribuye causa al layout ni a caché sinprueba.
  Se solicitó captura principal para distinguir5casillasKC_NO deausencia real.

- Captura principal aportada: confirma las87posiciones, incluidas5casillas vacías
  entre7 yBackspace. El usuario intentaba conservarles leyendas solo por estética;
  la no persistencia enesas5 es rechazo intencional, no fallo deguardado de sanas.
  Se decidió no habilitarlas ni falsear el mapa para una captura.
- Imagen de ventana revisada y publicada sin retoques, con excepción exacta en
  .gitignore ypie explicativo; error yotrosarchivos detmp siguenprivados.
- Commits e65d64f/53525fe/b7ee763 creados ypush verificado desdeMac. HTTPSsincredenciales
  falló; SSHpreexistente autenticado permitió push sin copiar credenciales. Solo
  pushURLlocal cambió aSSH; fetchHTTPSpermanece. Publicación no incluye OEM/builds.

## 2026-10-30 — Requisitos y reconstrucción pública afinados

- Por pedido del usuario, retiradas referencias narrativas a directorios privados
  irrelevantes, manteniendo exclusiones y la evidencia técnica completa.
- Requisitos separados por tarea; no se necesitan dos equipos/sistemas juntos.
  Se conservan restricciones reales de toolchain/backend y entornos ensayados,
  diferenciándolos de requisitos. Diagrama Mermaid del flujo en README.
- Registro de reconstrucción público con commit/hash de todas las fuentes,
  dependencias, parche, compilador, artefacto, geometría y límites de verificación.
  Fuentes verificadas contra el commit53525fe; no se publicaron builds ni OEM.
- Captura pública reemplazada por versión aportada con mejor zoom y mismo alcance:
 87posiciones dibujadas,5vacías/deshabilitadas,82útiles. Sin cambios de firmware.
