# Fuentes del firmware y variantes

Port experimental SonixQMK para HyperX Alloy FPS Pro HX-KB4RD1-US.
[Estado actual](../README.md), [límites](../docs/status-and-limits.md) y
[riesgos](../docs/safety-and-recovery.md) prevalecen sobre informes históricos.

## Qué está instalado

`keyboards/hyperx/alloy_fps_pro/keymaps/vial_editable/`: TKL ANSI, 82 posiciones
sanas (87 dibujadas), cuatro capas; parser Vial6/VIA9 reducido, mapa persistente por páginas y
marca USB pública de descubrimiento desktop. GUI, persistencia y restauración de
una prueba real verificadas. No es Vial-QMK completo ni firmware declarado estable.

La app se enlaza en **0x200**; el jumploader vive en los primeros512 B.
**La app binaria no debe escribirse desde cero.** Las actualizaciones ordinarias
preservan jumploader y bancos; una primera instalación es otro procedimiento.

## Variantes conservadas

| Variante | Propósito |
| --- | --- |
| `default` | Referencia compilada de 87 posiciones, primer arranque QMK comprobado. No replica OEM ni repara teclas. |
| `custom42` | Mapa estático de 42 posiciones, BASE/NUM/SYM/NAV. No importado del Silakka. |
| `custom42_fn` | Anterior más F1–F12, cuatro capas estáticas. |
| `raw_compact` | Experimento del transporte USB reducido para caber en RAM. |
| `vial_readonly` | Prototipo previo de identidad/definición/lectura; rechaza escrituras. No usarlo esperando edición. |
| `vial_editable` | Variante actual con backend físico y whitelist de asignaciones. |

`experiments/vial_store/` es el modelo host anterior, no un mapa de direcciones
para programar hardware. El backend físico actual está separado.

## Arquitectura relevante

- `jumploader/`: C/ASM y linker de arranque; proxy de vectores, Escape, solicitud
  magic e inspección de vectores. Entrada ISP observada, no garantía anti-brick.
- `vial_editable/protocol.c`: comandos admitidos; rechaza extras/reset/bootloader.
- `vial_editable/keymap.c`: lookup del mapa, whitelist y desbloqueo físico.
- `page_store.c/.h`: dos snapshots con CRC, generación y commit final.
- `flash_backend.c` y `map_reserve.ld`: geometría física y reserva de bancos.
- `definition.h` / `vial.json`: geometría TKL generada, separada de matriz eléctrica.
- `patches/qmk/` desde la raíz: parche de estructuras USB con preimágenes fijadas;
  no una actualización libre a cualquier revisión QMK.

El `EEPROM_DRIVER=transient` de la base no ofrece persistencia general QMK:
esta variante tiene un almacén específico para mapas. No inferir macros/settings
persistentes a partir de que se conserve una tecla.

## Compilar sin USB

Con el entorno [preparado y fijado](../docs/reproduction.md):

```sh
rtk proxy python3 -B scripts/build_compact_raw.py --keymap vial_editable
rtk proxy python3 -m unittest discover -s tests -v
rtk proxy python3 scripts/flash_trial.py --keymap vial_editable
```

El último comando es dry-run. El build genera binario/manifiesto privados en
`build/`; se comprueban hash de fuentes, memoria, vectores y límites. 21 412 B de
app, RAM1 968/2 048 B con pilas224/480 B, heap80 B; high-water no medido.
Cambiar una fuente, aunque sea un comentario, puede invalidar su manifiesto:
no saltar esa comprobación para usar un candidato antiguo.
