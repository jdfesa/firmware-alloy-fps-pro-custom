# Objetivo y reglas de este proyecto

Las reglas RTK se incluyen abajo para que este archivo sea portable y no
dependa de rutas personales de la máquina de desarrollo.

## Fuente única de trabajo

- La copia macOS local es la fuente principal elegida por el usuario. Linux
  remoto por SSH aporta el toolchain y **allí está conectado el HyperX**. No
  hace falta moverlo para código/build. GitHub es el punto de sincronización.
- El trabajo SSH inicial es la base; no descartarlo. Antes de sincronizar,
  comparar cambios y no sobrescribir archivos distintos sin revisión.
- README es la entrada única; los múltiples archivos forman un solo repo.
- Binarios y entornos Linux importados no son ejecutables nativos de macOS.
- Objetivo final obligatorio: detección y remapeo en Vial/QMK; cuatro capas
  estáticas compiladas no equivalen a haber completado ese objetivo.

## Qué buscamos

Crear firmware propio para el **HyperX Alloy FPS Pro HX-KB4RD1-US**, con unas
42 posiciones útiles y capas de números, símbolos y navegación. La base actual
es SonixQMK. **Vial es una segunda fase**, no una función ya implementada.
La configuración debe aproximarse al flujo del usuario en su Silakka54, no
suponer que ya se dispone de su mapa exacto.

## Límites obligatorios

- **No abrir, desmontar, soldar ni manipular internamente el HyperX.** El usuario
  lo rechazó expresamente por riesgo de daño. No volver a pedir fotos internas.
- **No tocar el Silakka54**: no flashearlo, reconfigurarlo, consultar su
  configuración ni capturar sus entradas. Solo usar una exportación si el
  usuario proporciona voluntariamente un archivo ya existente.
- Teclas averiadas reportadas: `8 9 0 - =`; Backspace funciona. El mapa
  `custom42` no utiliza esas posiciones. No prometer repararlas por firmware.
- Una autorización general para experimentar no valida un protocolo, offset
  o procedimiento de recuperación. No escribir un binario a ciegas.
- No quitar protección de lectura para obtener un backup: el MCU candidato
  puede borrar User ROM al desprotegerse. No usar unlock/unprotect/mass erase.
- No ejecutar el actualizador propietario ni su DLL. Analizarlos estáticamente.
- No sustituir el proyecto por un remapeador del PC o adaptador externo sin
  explicar la diferencia y acordar ese cambio de objetivo con el usuario.

## Estado verificado al 2026-10-29 — actualizado tras SSH

- OEM `0951:16d2`, `bcdDevice=2112`; puerto sysfs circunstancial, no identidad fija.
- Ciclo OEM→ISP→OEM verificado sin flash; usuario confirmó escritura posterior.
  Familia SN32F26x por protocolo, CS0, checksum0x27d1. MCU exacto/PCB aún inferidos.
- QMK `custom42`:17316 B, `default`:16868 B; nuevo `custom42_fn`:17316 B,
  cuatro capas,42+12 teclas, averiadas excluidas. Vial no integrado.
- RAM reservada1960/2048 B con pilas; heap88 B, máximos de pila no medidos.
- App en0x200. Jumploader propio C/ASM compilado436 B, relleno512, no instalado.
- 62 tests pasan en Linux y macOS. Sin backup de unidad ni rescate ante app
  inválida verificado.
- El ciclo previo por SSH en Linux dispuso de USB/hidraw; no asumir ese acceso
  en el host macOS actual. `probe_hyperx.py` es metadata-only por defecto;
  `--probe-cycle` cambia temporalmente de modo. Nunca capturar entradas ajenas.
- Checksum de imagen de referencia no coincide bajo cálculos ensayados; dominio
  ISP pendiente. NO declarar imagen idéntica, auténtica ni restaurable.
- Fuentes nuevas, evidencias y continuación: `docs/usb-isp-and-startup.md`.

## Presupuesto Vial

- Iluminación ya deshabilitada. Raw HID upstream con colas mínimas2392 B; sin tapping y
  serial constante2240 B, ambos exceden2048 B antes de Vial/mapa editable.
- `scripts/measure_raw_hid.py` reproduce ambos enlaces, solo build, no USB.
- El experimento preexistente `raw_compact` ya enlaza con el parche verificado
  de `patches/qmk`:18536 B flash,1952/2048 B RAM,96 B heap. Conserva tapping,
  cuatro capas y pilas224/480; no mide máximos de pila ni USB real.
- Nuevo `vial_readonly`:19460 B flash, misma RAM. Implementa identidad,
  definiciónXZ y lectura de mapa Vial6/VIA9; rechaza mutaciones/unlock/ISP.
  **No es Vial completo ni configurable ni detectado en hardware.** Leer
  `docs/vial-readonly-prototype.md`; la GUI puede aparentar un SET rechazado.
- Usuario acepta considerar3 capas si ayuda; mapas siguen en4. Quitar una capa
  estática ahorra flash, no resuelve el overflow RAM del transporte.
- Leer `docs/vial-memory-budget.md`. No declarar Vial integrado o detectado.
  El almacén C simulado ya está implementado: estado8 B, objeto ARM1272 B,
  29.266 casos de fallos simulados; no integrado ni backend físico. Leer
  `docs/vial-map-store.md`. Siguiente: geometría/recuperación y desgaste/latencia
  antes de adaptar escrituras; nunca usar los bancos virtuales como direcciones.

## Antes de continuar

1. Leer primero [el informe USB/arranque](docs/usb-isp-and-startup.md) y [la guía de continuación](docs/next-steps.md), que explica el arranque
   auxiliar sin asumir conocimientos de firmware.
2. Consultar [el informe ARM](docs/arm-build-and-boot.md), la
   [bitácora](docs/project-log.md) y `hardware/validation-status.json`.
3. La próxima investigación es **arranque, protocolo USB y recuperación con
   carcasa cerrada**, no reinstalar herramientas ni recompilar sin propósito. La exportación DLL ReadData es un wrapper de GET_FEATURE, no evidencia de lectura flash.
4. No cambiar validaciones a `true` por conveniencia. Vincular cada afirmación
   nueva con evidencia, alcance y limitaciones. Separar inferencias de hechos.

## Comandos y evidencias

Todas las órdenes de shell deben comenzar con `rtk`; usar `rtk proxy` si no
existe subcomando específico.

```sh
rtk proxy python3 -m unittest discover -s tests -v
rtk proxy python3 scripts/check_port_readiness.py
rtk proxy python3 scripts/build_firmware.py --keymap custom42
rtk proxy python3 scripts/build_firmware.py --keymap default
rtk proxy python3 scripts/build_firmware.py --keymap custom42_fn
rtk proxy python3 scripts/build_jumploader.py
rtk proxy python3 -B scripts/build_compact_raw.py --keymap vial_readonly
rtk proxy python3 -B scripts/measure_map_store.py
```

El comprobador devuelve **2 / NOT READY TO FLASH** mientras falten evidencias.
Solo informa: no es un mecanismo que autorice o ejecute escrituras.
Los builds requieren el entorno local preparado en `artifacts/tools`;
revisiones fijadas en `toolchains/build-lock.json`.

Documentar cada avance significativo en `docs/project-log.md` y actualizar la
guía/estado cuando corresponda. No afirmar «estable», «instalado», «recuperable»
o «backup» sin haberlo comprobado. No registrar números de serie, SP ni códigos
de la foto. Binarios propietarios, herramientas y builds locales quedan fuera
del versionado según `.gitignore`.

La ESP32 mencionada por el usuario es **una posibilidad a estudiar, no hardware
identificado ni autorización para programarla**. No asumir que cualquier ESP32
puede actuar como puente USB o programador del HyperX.

## Publicación

El usuario pretende publicar este proyecto en GitHub. Antes de añadir archivos,
leer [la revisión de publicación](docs/publication-review.md). Mantener excluidos
los binarios propietarios, herramientas, fotos de etiquetas, temporales y logs
locales. Solo cuatro JSON revisados de `artifacts/analysis` están permitidos por
`.gitignore`; no ampliar esa lista sin revisar contenido y rutas personales.
No publicar ni crear un repositorio remoto sin una petición explícita.
