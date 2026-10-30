# Actualización acotada desde macOS

> [!WARNING]
> Este transporte fue probado en una unidad. No es un flasher universal ni una
> restauración OEM. Leer primero [riesgos](safety-and-recovery.md) y
> [prerrequisitos](reproduction.md). Esta página trata actualizaciones de una
> unidad ya instalada; la primera instalación fue un procedimiento diferente.

## Separación de transportes

- RAW HID FF60/61: configuración Vial de la app, no instalación de firmware.
- ISP FeatureReport: consultas F260, programación acotada y retorno explícito.

El contrato [hidapi](https://libusb.info/hidapi/group__API.html) exige report ID
cero más 64 bytes en ambos buffers Feature. El adaptador exige 65 bytes, ACK yeco;
reutiliza la secuencia F260 revisada en [el primer ensayo](first-flash-trial.md).
No se ejecuta el actualizador propietario ni la herramienta upstream completa.

## Límites del adaptador

`flash_trial.py --mac` selecciona una única colección ISP 0c45:7010/release0100,
interfaz 0 (o -1 si hidapi no informa), y exige su ruta vigente explícita.
Rechaza ambigüedad o cambios al abrir. Solo enumera esa identidad y nunca abre
colecciones de teclado ajenas. La ruta es circunstancial, no identidad permanente.

Antes de programar verifica fuentes/manifiesto/binario, vectores, RAM, hash del
dry-run, familia F260 / CS0 y checksum previo explícito. Solo permite app desde 0x200
con fin <=0x7000, fuera de jumploader, bancos y región ISP reservada. No admite
primera instalación en Mac, OEMentry, borrado explícito, cambio de protección,
reintentos de escritura ni reinicio automático. ACK/eco no son readback de flash.

## Secuencia usada en esta unidad

1. Cerrar clientes por completo. Guardar un snapshot privado del mapa y revisar
   su preimagen; esto no es un backup OEM.
2. Dry-run del candidato con fuentes/manifiesto actuales. No reutilizar hashes
   ni checksums de una sesión anterior como autorización.
3. Conectar solo el HyperX manteniendo Escape para entrar al ISP. Observarlo y consultar
   versión/CS0/checksum; indicar cuándo soltar Escape. No programar por enumerar.
4. Tras revisar candidato/rango, enviar una sola secuencia con SHA  y checksum
   explícitos. Ante error, detener sin retry/reboot ni desconexión durante escritura.
5. Si se completó, pedir retorno explícito con checksum actual ysin Escape.
   Comprobar app, definición  y mapa; no abrir otro cliente hasta cerrar el diagnóstico.
6. Abrir Vial y verificar visualización, edición trasUnlock, reconexión y salida.
   Restaurar cambios de prueba sin sobrescribir ediciones ajenas.

No publicar una orden de apply con valores copiados de esta unidad como receta
para otro teclado. Los flags ycontroles se pueden estudiar con `--help`; ninguna
comprobación constituye una garantía universal.

## Qué se verificó

- Transporte realMac F260 / CS0, ACK/eco  y retorno en tres actualizaciones app-only.
- TKL inicial de 82 posiciones visibles  y mapa anterior preservado.
- Corrección del descriptor público para detección desktop.
- EdiciónGUI de 3 teclas, reconexión física, lectura896 B ysalidaFn+A; restauraciónGUI
  atransparentes  y base completa recuperada.
- Gráfico posterior de 87 posiciones, mismas82 útiles, definición416 B  y mapa intacto.
- 107 tests completos pasan en el entorno Mac preparado. No estabilidad prolongada,
  recuperaciónOEM, desgaste oapp deliberadamente corrupta demostrados.

La causa de algunos timeoutsRAW no se aisló. Cerrar clientes yreconectar permitió
continuar, pero no se presenta como diagnóstico definitivo ni fiabilidad resuelta.
Datos exactos de imágenes  y checksum en `hardware/first-flash-evidence.json`.
