# Primer ensayo acotado de programación

> [!NOTE]
> Informe de una fase anterior, conservado por su evidencia y fuentes. No usar
> sus estados provisionales como estado actual ni sus comandos como receta universal.
> Leer primero [README](../README.md), [estado](status-and-limits.md) y
> [seguridad/recuperación](safety-and-recovery.md).

2026-10-30. Procedimiento experimental; los resultados reales se registran aparte.
No equivale a backup, restauración OEM, Vial editable ni estabilidad validada.

## Evidencia mínima revisada

- SONiX SN32F260 User Manual v1.9 §11.4, p.122: páginas de64 B; User ROM
  `[0,0x7800)` (480 páginas), Boot Loader `[0x7800,0x8000)` (32 páginas).
  §11.6 permite borrado por página; §11.7 describe ISP USB; §11.8.2/3 separa
  program/erase de página de desprotección con mass erase. Se inspeccionó la
  tabla renderizada, no se dedujeron límites de un tamaño de archivo.
  [Manual SONiX, copia conservada por Crossic](https://crossic.com/wp-content/uploads/2021/10/SN32F264_V1.9_EN.pdf).
- [SonixFlasherC73f9fab8 src/main.c](https://github.com/SonixQMK/SonixFlasherC/blob/73f9fab8a82c5c4f91181d276676c8f936726925/src/main.c),
  líneas162–176: **omite CMD_ENABLE_ERASE para F260**. No confundir con
  `flash_erase()` aislada, que sí construye un borrado de toda la región.
- [src/flash.c de esa revisión](https://github.com/SonixQMK/SonixFlasherC/blob/73f9fab8a82c5c4f91181d276676c8f936726925/src/flash.c):
  CMD5=`0x0055aa05`, offset enbytes en+4, cantidad de reportes64B en+8,
  ACK `0xfafafafa`, stream de datos; respuesta final devuelve el último word
  en+60. [Versión anterior b41694c](https://github.com/SonixQMK/SonixFlasherC/blob/b41694cdff5b6d935b51067f24975aabeebe344c/sonixflasher.c)
  también omite erase para F260. Eso sustenta el protocolo; no es una traza
  previa de escrituras de nuestra unidad ni prueba de preservación byte a byte.
- El perfil20/02 observado en la unidad es F260; CS0 observado. El nuevo
  instalador aborta ante otro chip/nivel. No ofrece comandos2/3/4/8/9, cambios
  de opciones, unlock ni erase. No se ejecuta el flasher upstream ni el OEM.
- Arranque mínimo existente: vectores en0, proxy de excepciones hacia0x200,
  Escape inferido C0/A0 antes de ejecutar QMK, magic `DEADBEEF` y rechazo de
  vectores inválidos. Dirección ISP `0x1fff0009` coincide con la referencia
  SonixQMK y el salto inferido del OEM. La tabla del manual identifica la
  región física a conservar; no se afirma que el ISP sea ROM inmutable.

## Imagen y alcance

Primera imagen = jumploader validado de512 B + app QMK `default` en0x200,
rellenada conFF únicamente hasta el siguiente bloque64 B. `default` es la
alternativa inglesa mínima del proyecto; no repara8/9/0/-/= ni restaura OEM.
No se instala el jumploader solo sobre el OEM. Las iteraciones posteriores
empiezan en0x200 y no incluyen esos primeros512 B. Ninguna imagen puede llegar
al ISP en0x7800. No se borra explícitamente ninguna región.

`scripts/flash_trial.py` es nuevo y separado del diagnóstico allowlist.
Por defecto **solo prepara/valida en memoria**, sin abrir USB. Revalida hashes
binario/fuentes, vectores, límites, padding y RAM desde manifests de build.
`--apply` exige puerto físico, SHA256 exacto del dry-run y checksum previo.
Selecciona exclusivamente HyperX/ISP en interfaz0, verifica el nodo al abrir,
F260/CS0 y checksum antes de CMD5. Sin reintentos de escritura ni reboot automático.

**Verificación limitada:** el ACK final y eco no prueban lectura de flash.
Se registran checksum devuelto y sum16 local sin fingir que el dominio está
resuelto. La discrepancia del checksum OEM no obliga a reconstruir el OEM.
Cualquier error detiene la secuencia y deja ISP, si sigue respondiendo, para
inspección. No desconectar mientras se programa. Una caída durante la primera
reescritura de arranque puede dejarlo sin rescate cerrado.

## Secuencia del ensayo

1. Dry-run `rtk proxy python3 scripts/flash_trial.py --first-install --keymap default`.
2. Revisar hash/rango concretos; `--apply` solo con los valores recién observados
   y autorización de esta sesión. Logs privados en `build/trial/`.
3. Tras completar sin error, **mantener Escape del HyperX** y pedir retorno
   desde ISP. Consultar otra vez ISP antes de liberar Escape: es la primera
   comprobación real del arranque independiente de QMK.
4. Liberar Escape, volver a user, observar VID/PID QMK y pedir escritura humana.
5. Hacer un ciclo físico: desconectar/reconectar solo HyperX con Escape pulsado,
   consultar ISP; luego arrancar normalmente. No tocar Silakka54.
6. Solo con rescate funcional, cambiar la app manteniendo el jumploader.
   Vial read-only puede comprobar transporte/detección pero no edición.

El checklist general conserva las evidencias aún pendientes. La aceptación del
riesgo residual permite este ensayo, no cambiar los indicadores anticipadamente.

## Resultados observados de la primera escritura

- Conjunto17408B,272reportes, rango `[0,0x4400)`, SHA256
  `78f0fa942cec435ebe7eaaea4d160b79b9cc5e961d3c3792e6c9155cc4441173`.
- F260/CS0/checksum0x27d1 reconfirmados antes de CMD5. ACK final y eco
  correctos; checksumposterior0x1ad2 frente asum16local0xc98f: **no readback**.
- RETURN_USER con Escape pulsado: reenumeración0c45:7010/bcd0100, versión y
  checksumISP respondieron. Al soltarEscape y repetir retorno: QMK enumera
  FEED:A11F/bcd0001, producto Alloy FPS Pro custom EXPERIMENTAL.
- Usuario escribió `hola qmk`. Después desconectó/reconectó solo HyperX con
  Escape; ISP reenumeró y respondió F260/CS0/checksum0x1ad2. QMK Bootmagic
  también está habilitado: no atribuir exclusivamente esta entrada al
  jumploader sin aislarlo. No prueba de app deliberadamente corrupta.
- Datos públicos saneados: `hardware/first-flash-evidence.json`. No incluye
  serial, ruta de hidraw, puerto privado ni credenciales.
