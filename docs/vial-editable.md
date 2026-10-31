# Vial editable experimental: páginas físicas y cuatro capas

Resultados de hardware: **2026-10-30**. Candidato TKL instalado desde macOS;
edición GUI, persistencia y restauración verificadas sobre una unidad.
Consultar [estado y límites](status-and-limits.md) y
`hardware/first-flash-evidence.json` para distinguir compilación y pruebas reales.
No es Vial-QMK completo ni firmware declarado estable.

## Configuración y geometría actuales

El gráfico ANSI TKL muestra 87 posiciones en seis filas físicas, con anchos
reales y bloque de navegación. Hay 82 utilizables: `8 9 0 - =` siguen en
`KC_NO` y no aceptan asignaciones no nulas. Las casillas vacías representan
posiciones averiadas, no teclas ausentes del dibujo ni reparadas por firmware.

La base inglesa conserva Enter, Backspace y navegación. Hay cuatro capas;
1–3 son transparentes inicialmente y Fn usa `MO(1)`. Se pueden editar las
posiciones admitidas y sus asignaciones de capa. Usar una zona de 42 teclas es
una elección de distribución, no un requisito de hardware ni de Vial.

`scripts/generate_vial_editable.py` genera la geometría física sin cambiar la
matriz eléctrica 14×8, el UID o los mapas. Conserva identidad propia, sin imitar
el VID/PID de otro teclado. La definición reside en flash, no en otro mapa RAM.
La cuadrícula eléctrica y el dibujo con solo 82 posiciones son revisiones
anteriores; la cronología de abajo conserva sus resultados por separado.

## Desbloqueo y edición desde la GUI

El firmware exige desbloqueo para **todas** las escrituras. La GUI de referencia
solo lo solicita automáticamente para RESET; para teclas normales puede mostrar
optimistamente un cambio rechazado. Procedimiento:

1. Abrir un solo cliente Vial y seleccionar el HyperX.
2. Elegir **Security → Unlock**; en macOS está en la barra de menús superior.
3. Mantener **Tab + Caps Lock físicos** hasta completar la barra; después soltar.
   El GUI de referencia consulta cada 200 ms: 20 pasos son unos 4 s. Pulsar las
   teclas sin iniciar Unlock no abre el desbloqueo.
4. Seleccionar capa y tecla en el dibujo superior; elegir la asignación con el
   mouse en el selector inferior. No se asigna escribiendo con la tecla física.

Cada asignación admitida se guarda automáticamente. No requiere botón final,
compilar C, reflashear ni dejar Vial abierto. Reconectar vuelve a bloquear
escrituras, pero no borra el mapa ni impide usarlo. Desbloquear de nuevo antes
de editar; no hace falta repetir Unlock por cada asignación.

No es unlock/unprotect del MCU y no cambia protección flash. El combo depende
de coordenadas físicas, no de sus remapeos. Durante el progreso se limpian
reportes y se bloquean pulsaciones de uso; no se expone la matriz ni se capturan
entradas. No es autenticación criptográfica.

Si el nombre del menú difiere según versión, buscar el desbloqueo, no reset,
bootloader o borrado. Confirmar cambios por relectura y reconexión, no solo por
el dibujo. No mantener varios clientes abiertos. Ver [uso diario](usage.md).

## Protocolo y funciones admitidas

Vial 6 / VIA 9 de la referencia fijada. SET_KEYCODE y SET_BUFFER (hasta 28 B)
escriben el mismo almacenamiento que lee el escaneo QMK. Keycodes admitidos:
básicos 0/1, 04..73, E0..E7, modificadores, mod-tap, LT de 0..3 y TO/MO/TG de
0..3. Se rechazan códigos no compatibles, posiciones deshabilitadas, comandos
boot/reset y extras. La GUI puede mostrar optimistamente un SET rechazado.

One-shot Shift, multimedia/volumen, macros, combos, tap-dance, encoders,
iluminación y QMK Settings no están implementados o admitidos en esta variante.
Un mapa procedente de otra matriz no es importable 1:1. Elegir sustitutos para
funciones no admitidas, sin eliminarlas silenciosamente durante una conversión
ni prometer compatibilidad total. Ampliarlas requiere desarrollo y mediciones;
no se garantiza que cualquier extensión quepa en 2 KB de RAM.

## Geometría y reserva de flash

El modelo previo en `firmware/experiments/vial_store` usa palabra de 4 B y erase
FF: **no se conectó ese contrato directamente al MCU**. El manual SONiX v1.9
§11.1 describe erase a 0; el backend físico no depende de esa polaridad.
Fuentes y tabla en [primer ensayo](first-flash-trial.md). Registros FMC §11.11:
base 0x40062000, STATUS +4, CTRL +8, DATA +12, ADDR +16; PER=2, PG=1, START=64.

- Arranque `[0,0x200)` e ISP `[0x7800,0x8000)` quedan fuera del backend.
- El ASSERT del linker exige fin de imagen <=0x7000; build e instalador también
  comprueban ese límite.
- Dos bancos físicos: `[0x7000,0x7400)` y `[0x7400,0x7800)`.
- Cada banco: header de 64 B (magic AVP2/esquema/generación/CRC), mapa de 896 B
  en 14 páginas y commit de 64 B separado (CMIT/generación/CRC y ceros restantes).
- No programa palabras repetidamente en una página. Reemplaza exactamente 64 B
  con erase de esa página y PG completa, verificando lectura de los 16 words.
- Invalida primero el commit destino; escribe 14 páginas del mapa y header;
  valida CRC y códigos; publica el commit final. Nunca escribe el banco activo.
- Al arrancar elige el banco válido más nuevo (generaciones adyacentes, rollover);
  si ninguno es válido, usa defaults sin escribir. La atomicidad simulada es
  por paquete, no por importación entera. CRC no autentica ni elimina todo fallo.

El MCU se detiene durante erase/program (§11.1); se preserva PRIMASK y se inhiben
interrupciones durante cada reemplazo. Se comprueban BUSY acotado, ERR y readback.
No modifica LPCTRL, opciones, seguridad o ISP. Un fallo bloquea escrituras y
remonta bancos. No se añadieron buffers heap ni un mapa de 896 B en RAM: estado
de 8 B y buffer de 64 B en pila. Las pilas de 224/480 B se conservan; sus máximos
reales siguen sin medir.

Build TKL comprobado: app de 21 412 B, RAM reservada 1968/2048 B y heap de 80 B.
Imagen app-only de 21 440 B, 335 reportes, rango `[0x200,0x55c0)`.
Los hashes de los candidatos ensayados están en la evidencia, no se deducen del
nombre ni se actualizan por una edición posterior de documentación.

## Latencia, desgaste y pruebas host

Una edición distinta hace 17 reemplazos de página (commit destino dos veces).
No-op no escribe. Manual v1.9 p.130 indica 5 ms típicos de erase y 5 ms de
program: estimación previa de 170 ms/transacción, **no garantía de latencia**.
Se escribe por edición explícita, nunca por pulsaciones normales. El mínimo
especificado es 10k ciclos; 100k figura como referencia no verificada. El commit
recibe más desgaste: no usar cambios de mapa continuos como animación o macros
de configuración. Importaciones grandes requieren muchas transacciones.

Los tests host usan C real del almacén, mapa, adaptador y parser: 52.275 casos
de cortes por bits durante los 17 reemplazos, desde defaults y ambos bancos,
además de sanitizers. Solo admiten resultado viejo o nuevo y banco activo intacto.
No cubren brownout que dañe otra página, desgaste real ni USB/pilas en ejecución.

## Cronología de validación — 2026-10-30

### Edición por herramienta, antes de la geometría TKL

La definición inicial de 376 B dibujaba la cuadrícula eléctrica. La herramienta
`probe_vial.py --mac` seleccionó únicamente FEED:A11F/usage FF60:61, nunca la
colección de teclado. Un timeout desapareció al cerrar otros clientes y
reconectar; no se aisló la causa ni se declaró resuelta la fiabilidad general.

1. Identidad, definición y mapa de cuatro capas coincidieron con la evidencia previa.
2. Tras Tab+Caps se envió SET_KEYCODE: Q[0,2,1] 0x0014→Z 0x001d.
3. ACK en 269 ms; relectura completa de 896 B idéntica salvo esa tecla.
4. Desconexión/reconexión sin Escape: Q escribió `z` y RAW conservó el mapa.
5. Otro desbloqueo restauró Q en 266 ms. Tras reconectar se confirmó `q`, el
   hash original del mapa y el estado bloqueado.

Esta prueba comprobó el núcleo por protocolo, **no edición desde GUI**. No
cambió app, jumploader o ISP ni se ejecutó el updater propietario. Evidencia en
`hardware/first-flash-evidence.json`; snapshot privado previo en
`build/trial/mac-q-to-z.json`. El script no sobrescribe una prueba existente.

### Instalación del TKL y comprobación de rescate

El transporte `flash_trial.py --mac` usa ISP FeatureReport, no RAW. Escape entró
al ISP con Bootmagic de la app deshabilitado, aislando la ruta del jumploader.
F260/CS0 y checksum previo 0xeb27 comprobados; se enviaron 335 reportes una sola
vez, ACK/eco correctos y checksum posterior 0x9ac7. El retorno explícito sin
Escape confirmó TKL de 416 B y mapa completo de 896 B idéntico al snapshot previo.
No se reescribieron arranque, bancos o ISP; no hubo readback completo de flash.
[Procedimiento y límites del transporte](usb-update.md).

### Descubrimiento desktop, edición GUI y restauración

Se corrigió el descriptor heredado EXPERIMENTAL. El
[GUI fijado e42622c](https://github.com/vial-kb/vial-gui/blob/e42622c352b69eff523a467718db487ab9c9cbf2/src/main/python/util.py)
busca `vial:f64c2b3c` o un dispositivo VIA registrado/sideload. Se añadió esa
constante pública, no un serial privado. App de 21 412 B, RAM de 1968 B, misma
definición, UID, VID/PID y bancos; 106 tests pasaron en macOS en esa revisión.

Otra actualización app-only en `[0x200,0x55c0)`, 335 reportes, tuvo ACK/eco
correctos y checksum 0x9ac7→0x53cd. Tras reconexión física se confirmó detección
en Vial desktop. Una lectura RAW inicial agotó timeout; la causa no se aisló.

Desde GUI, tras Security → Unlock, se asignó E a A/S/D de **capa 1**. Relectura
de 896 B confirmó solo esas tres posiciones 0x0001→0x0008 (no Q→Z). Tras
reconectar sin Escape, el mapa siguió idéntico, volvió el bloqueo y Fn+A escribió E.
Otro Unlock permitió restaurar las tres posiciones a transparentes desde GUI;
una nueva reconexión confirmó los 896 bytes originales y el estado bloqueado.
El aparente fallo de restauración era omitir Unlock después de reconectar.

### Gráfico de 87 posiciones, sin habilitar las cinco averiadas

Se añadieron las cinco posiciones al dibujo, manteniendo `KC_NO` y el rechazo
de asignaciones no nulas. No cambió UID, matriz o persistencia. Definición de
416 B, app de 21 412 B y RAM de 1968 B; 107 tests pasaron en macOS. Nueva
actualización app-only de 335 reportes en `[0x200,0x55c0)`, con ACK/eco y retorno
correctos. RAW confirmó 87 coordenadas y mapa de 896 B idéntico a la base.
Las cifras anteriores de 82 posiciones visibles pertenecen a la revisión previa.

## Alcance de la recuperación

Escape al conectar se comprobó con Bootmagic de la app deshabilitado. No se
probó una app deliberadamente corrupta, desgaste real o estabilidad prolongada;
no hay backup/restauración OEM. En nuevas pruebas, comprobar rescate y base,
releer el mapa antes/después de reconectar y verificar salida HID humana.
Restaurar cambios de prueba sin sobrescribir configuraciones ajenas.
