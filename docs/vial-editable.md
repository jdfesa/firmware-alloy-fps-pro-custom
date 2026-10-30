# Vial editable experimental: páginas físicas y cuatro capas

2026-10-30. Candidato TKL instalado desde macOS; edición GUI persistente verificada.
Consultar hardware/first-flash-evidence.json para
separar compilación de pruebas reales. No es todo Vial-QMK: sin macros, combos,
encoders, iluminación, ajustes QMK ni comandos de arranque remotos.

## Prueba real en macOS — 2026-10-30

El candidato de definición eléctrica376B ya estaba instalado al retomar.
`probe_vial.py --mac` seleccionó únicamente FEED:A11F/usageFF60:61, nunca la
colección de teclado ni el Silakka54. Un timeout inicial desapareció al cerrar
los otros clientes y reconectar; no se aisló la causa ni se considera resuelta
la fiabilidad de conexión. Después se verificó:

1. Identidad/definición/mapa de cuatro capas coincidentes con la evidencia previa.
2. Desbloqueo físico Tab+Caps; SET_KEYCODE de Q[0,2,1]0x0014→Z0x001d.
3. ACK en269ms y relectura completa896 B idéntica salvo esa tecla.
4. Usuario desconectó/reconectó sin Escape: Q escribió `z`; RAW conservó el mapa.
5. Nuevo desbloqueo; restauración deQ en266ms. Otra reconexión: usuario confirmó
   `q` y RAW recuperó el hash del mapa original. El dispositivo volvió bloqueado.

**Esta prueba histórica comprobó el núcleo; la pruebaGUI posterior está abajo.** No se
cambió la aplicación, el jumploader ni el ISP durante estas dos transacciones.
No se ejecutó el updater propietario ni se accedió al Silakka54 físico.
Evidencia pública saneada en `hardware/first-flash-evidence.json`; copia privada
previa del mapa en `build/trial/mac-q-to-z.json`, que no debe borrarse durante
una prueba pendiente. El script se niega a sobrescribir una prueba existente.

## Por qué no editaba la GUI y cómo operar

El firmware exige desbloqueo para **todas** las escrituras. La GUI de referencia
solo lo solicita automáticamente para RESET; para teclas normales puede mostrar
optimistamente un cambio que fue rechazado. Elegir explícitamente
**Security → Unlock**, mantener **Tab + Caps Lock físicos** durante el progreso
(aproximadamente2s), soltar y recién después editar. Al reconectar hay que
volver a desbloquear. No es unlock/unprotect del MCU: no cambia protección flash.
Si el nombre del menú difiere según versión, buscar la opción de desbloqueo;
no usar reset, bootloader o borrado como sustituto. Confirmar cambios releyendo
tras reconectar; no confiar solo en el dibujo. No dejar varios clientes abiertos.

La geometría instalada es una cuadrícula eléctrica14×8, no una mitad de un
teclado dividido. El generador nuevo `scripts/generate_vial_editable.py` coloca
las 82 teclas sanas en seis filas físicas ANSI TKL, con anchos reales y bloque
de navegación. Conserva identidad propia, matriz y mapas; no imita el VID/PID
del Silakka ni de otro fabricante. Los cinco espacios averiados se mantienen
como huecos, sin ofrecer teclas inexistentes o prometidas como reparadas.
La definición está en flash, no ocupa un mapa nuevo en RAM. Build real TKL:
21 412 B de app,1968/2048B reservados,80B de heap y pilas224/480 sin reducir.
Imagen app-only21440B,335 reportes, rango `[0x200,0x55c0)`. Hashes en la evidencia.
**Instalada en esta sesión:** el nuevo transporte `flash_trial.py --mac` usa
FeatureReportISP, no RAW. Escape entró al ISP con Bootmagic de app deshabilitado;
F260 / CS0  y checksum previo0xeb27 comprobados.335 reportes enviados una sola vez,
ACK/eco correctos, checksum posterior0x9ac7. Retorno explícito sin Escape confirmó
TKL416 B y los896 B del mapa idénticos al snapshot previo. No reescritura dearranque,
bancos oISP; no lectura completa de flash. [ProcedimientoMac](usb-update.md).
Edición posterior desdeVialdesktop y salida humana verificadas como se detalla abajo.

## Referencia voluntaria del Silakka54

Se leyó únicamente el [respaldo público ofrecido por el usuario](https://github.com/jdfesa/mydotfiles/tree/main/hardware/silakka54).
Usa cuatro capas con asignaciones útiles y otras transparentes; sirve como
referencia ergonómica de42 posiciones usadas, no como archivo importable1:1
sobre otra matriz. Básicos, símbolos con modificadores, mod-tap y layer-tap
0..3 entran en el subconjunto actual. **One-shot Shift y multimedia/volumen**
presentes en esa referencia no están admitidos; tampoco macros/combos/tap-dance.
No eliminar silenciosamente esas funciones ni prometer una copia exacta.
El mapa final de42 teclas debe acordarse; por ahora se conserva base inglesa82.

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
mientras la GUI consulta progreso. Reconexión bloquea otra vez. El combo usa
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
- Cada banco: header64B (magicAVP2/esquema/generación/CRC), mapa896 B en14páginas,
  commit64B separado con CMIT/generación/CRC y ceros restantes.
- No programa palabras repetidamente enuna página. Reemplaza exactamente64B con
  erase deesa página yPG completa, verificando lectura de los16words.
- Invalida commit destino primero; escribe14páginas del mapa, header; validaCRC
  y códigos; publica commitfinal. Nunca escribe elbanco activo.
- Al arrancar elige banco válido más nuevo (generaciones adyacentes, rollover);
  si ninguno es válido, defaults sin escrituras. La garantía simulada es por
  paquete, no por importación entera. CRC no autentica ni elimina todo fallo.

El MCU se detiene durante erase/program (§11.1); se preservaPRIMASK y se inhiben
interrupciones durante cada reemplazo. BUSY acotado y ERR/readback se comprueban.
No tocaLPCTRL/opciones/seguridad/ISP. Un fallo bloquea escrituras yremonta bancos.
No se añadieron heap buffers ni mapas896 B enRAM: estado8B y buffer64B enpila.
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
inofensiva, releer, desconectar/reconectar sin Escape y verificar tantoVial como
salidaHID. Revertir la tecla para dejar una base utilizable.

## Vial desktop: detección y edición persistente verificadas

Se corrigió un defecto de descubrimiento: la variante heredaba el descriptor
textualEXPERIMENTAL. [VialGUIe42622c](https://github.com/vial-kb/vial-gui/blob/e42622c352b69eff523a467718db487ab9c9cbf2/src/main/python/util.py)
`find_vial_devices` busca la marca pública `vial:f64c2b3c`, o un dispositivoVIA
registrado/sideload. Se añade solo esa constante a la variante editable; no es
serial privado deunidad ni suplantación deotro teclado. App21 412 B, RAM1 968 B,
misma definiciónTKL, UID, VID/PID y bancos.106 tests pasan en Mac.

Nueva app-only instalada en[0x200,0x55c0),335 reportes; ACK/eco correctos,
checksum0x9ac7→0x53cd. MarcaUSB observada; usuario confirmó detección endesktop
tras reconexión física. Una lecturaRAW larga inicial agotó timeout; no se atribuye
causa única ni se declara resuelta la fiabilidad general.

Después deabrir **Security → Unlock enla barra superior de macOS**, mantener
Tab+Caps hasta completar labarra. Pulsar las teclas sin iniciar esa ventana no
hace nada. El GUIoficial consulta cada200ms, por lo que20 pasos son unos4s.
La edición usa mouse: seleccionar tecla destino eneldibujo superior y luego
la asignación enelselector inferior; no escribir conelteclado físico.

Prueba real: elusuario asignóE aA/S/D de **capa1**. Relectura896 B confirmó solo
esas tres posiciones0x0001→0x0008 (noQ→Z). Después dereconectar sin Escape,
relectura completa idéntica, relock y salidaFn+A→E confirmada porelusuario.
El usuario restauró las tres posiciones a transparentes desde GUI tras repetir
Unlock. Otra reconexión confirmó los 896 bytes originales y el estado bloqueado.
El aparente fallo al restaurar era haber omitido Unlock después de reconectar.

**Uso normal:** cada asignación admitida se guarda automáticamente. No requiere
botón final degrabar, compilarC, reflashear ni Vialabierto alusar elteclado.
Unlock solo esnecesario paraeditar después decada reconexión; no parausar elmapa.
C/recompilación son necesarios paraañadir funciones noadmitidas, sin prometer
que cabrá cualquier extensión en2KB. No macros/combos/tap-dance/multimedia,
one-shot o iluminación. Remapeos básicos, modificadores/mod-tap, LT0..3 y
TO/MO/TG0..3 siguen siendo el subconjunto permitido; no escoger códigos deotras
funciones suponiendo que se guardarán. Una pruebaGUI no valida todos loscódigos.

## Gráfico físico completo sin cambiar el mapa

Por pedido estético se dibujan ahora las 87 posiciones. Las82 sanas conservan su
comportamiento; las 5 averiadas siguenKC_NO yla whitelist rechaza habilitarlas.
No se cambiaron UID/matriz/persistencia. Definición de 416 B, app21 412 B  y RAM1 968 B,
107 tests pasan en Mac. Nueva app-only 335 reportes, mismo rango[0x200,0x55c0),
ACK/eco  y retorno correctos. RAW confirmó87 coordenadas  y mapa896 B idéntico a la base.
Las cifras82 visibles anteriores pertenecen a la revisión anterior del dibujo.
