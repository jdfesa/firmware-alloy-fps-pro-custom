# Vial editable experimental: páginas físicas y cuatro capas

2026-10-30. Candidato nuevo; consultar hardware/first-flash-evidence.json para
separar compilación de pruebas reales. No es todo Vial-QMK: sin macros, combos,
encoders, iluminación, ajustes QMK ni comandos de arranque remotos.

## Base y protocolo

82 posiciones útiles: base inglesa completa de87 excluyendo8/9/0/-/=.
Enter/Backspace/navegación se conservan. Cuatro capas;1..3 transparentes al inicio,
Fn=MO(1). El usuario puede editar las teclas visibles y selectores de capa.
El número42/54 no es una restricción permanente. Mapa sin exportación delSilakka54.

Vial6/VIA9 de la referencia fijada; SET_KEYCODE y SET_BUFFER (hasta28B) con
lectura del mismo almacenamiento por el escaneo QMK. Keycodes admitidos:
básicos0/1,04..73,E0..E7,mods/mod-tap,LT de0..3 yTO/MO/TG de0..3. Códigos
no compatibles, posiciones deshabilitadas, comandosboot/reset y extras rechazados.
La GUI podría mostrar optimistamente un rechazo: comprobar relectura/reconexión.

Lock físico: iniciar Unlock enVial y mantener **Tab+Caps** aproximadamente2s
mientras laGUI consulta progreso. Reconexión bloquea otra vez. El combo usa
coordenadas físicas, no lo cambian los remapeos. Unlock limpia reportes y bloquea
pulsaciones de uso mientras está enprogreso; no expone matriz ni captura entradas.
No es autenticación criptográfica. La persistencia requiere unlock previo.

## Geometría y reserva

El modelo previo en firmware/experiments/vial_store usa palabra4B y eraseFF:
**no se conectó ese contrato directamente al MCU**. ManualSONiXv1.9 §11.1
incluso describe erase a0; el backend nuevo no depende de esa polaridad.
Fuentes primarias y tabla en docs/first-flash-trial.md. RegistrosFMC §11.11:
base0x40062000,STATUS+4,CTRL+8,DATA+12,ADDR+16; PER=2,PG=1,START=64.

- Arranque `[0,0x200)` eISP `[0x7800,0x8000)` quedan fuera del backend.
- Linker ASSERT exige fin de imagen<=0x7000; build/instalador también comprueban.
- Dos bancos físicos: `[0x7000,0x7400)` y`[0x7400,0x7800)`.
- Cada banco: header64B (magicAVP2/esquema/generación/CRC), mapa896B en14páginas,
  commit64B separado con CMIT/generación/CRC y ceros restantes.
- No programa palabras repetidamente enuna página. Reemplaza exactamente64B con
  erase deesa página yPG completa, verificando lectura de los16words.
- Invalida commit destino primero; escribe14páginas delmapa, header; validaCRC
  y códigos; publica commitfinal. Nunca escribe elbanco activo.
- Al arrancar elige banco válido más nuevo (generaciones adyacentes, rollover);
  si ninguno es válido, defaults sin escrituras. La garantía simulada es por
  paquete, no por importación entera. CRC no autentica ni elimina todo fallo.

El MCU se detiene durante erase/program (§11.1); se preservaPRIMASK y se inhiben
interrupciones durante cada reemplazo. BUSY acotado y ERR/readback se comprueban.
No tocaLPCTRL/opciones/seguridad/ISP. Un fallo bloquea escrituras yremonta bancos.
No se añadieron heap buffers ni mapas896B enRAM: estado8B y buffer64B enpila.
Las pilas224/480B se conservan; máximos reales siguen sin medir.

## Latencia, desgaste y alcance

Una edición distinta hace17reemplazos de página (commitdestino dosveces).
No-op no escribe. Manualv1.9 p.130 indica5ms típicos erase y5ms program, porlo
que la estimación previa es170ms/transacción; **medir en unidad**, no garantía.
Escribe solo ante edición explícita, nunca por pulsaciones normales. El mínimo
especificado es10k ciclos;100k está marcado como referencia no verificada.
El commit recibe más desgaste: no usar este prototipo para actualizaciones
continuas/macros de configuración. Importaciones grandes hacen muchas transacciones.

Tests host usan C real delalmacén, mapa, adaptador yparser;52.275 casos de cortes
porbits durante erase/program de los17reemplazos, desde defaults yambos bancos,
y sanitizers. Solo se permiten resultado viejo o nuevo y bancoactivo intacto.
No cubren brownout que dañe otra página, desgaste real ni USB/stack en ejecución.

## Recuperación y prueba

El candidato deshabilita Bootmagic deQMK: Escape al conectar depende del
jumploader, no delmismo escaneoQMK. Probar esaentrada tras instalarlo.
Antes de pruebas de escritura, comprobar baseinglesa/GUI; cambiar una tecla
inofensiva, releer, desconectar/reconectar sinEscape y verificar tantoVial como
salidaHID. Revertir la tecla para dejar una base utilizable.
