# Estado, capacidades y límites del HyperX

Actualizado: 2026-10-30. Este es un firmware experimental independiente basado
en SonixQMK, con un subconjunto propio del protocolo Vial. No es un port completo
de Vial-QMK ni una restauración del firmware original de HyperX.

## Qué se consiguió y cómo se comprobó

- Firmware instalado y teclado capaz de escribir. Hay 82 posiciones útiles de
  un TKL ANSI; el gráfico muestra las 87 posiciones, pero las cinco averiadas
  (8, 9, 0, -, =) siguen deshabilitadas y no se ofrecen para remapear.
  El firmware no las reparó ni se promete repararlas.
- Cuatro capas y remapeo desde Vial de escritorio. La GUI web también mostró
  el TKL completo. La marca USB pública de descubrimiento se corrigió para que
  la aplicación de escritorio lo encuentre sin una definición cargada a mano.
- Edición real desde la GUI: el usuario asignó E a A/S/D de capa 1. Se leyeron
  los 896 bytes del mapa antes y después de desconectar/reconectar: idénticos.
  El teclado volvió bloqueado y Fn+A escribió E en un editor de la Mac.
  No presentar esta prueba como Q→Z: ese fue un ensayo anterior por script.
- Actualización desde macOS por transporte ISP FeatureReport. Dos aplicaciones
  se instalaron en [0x200, 0x55c0), dejando fuera arranque, bancos del mapa y
  región reservada. ACK/eco y retorno comprobados; no lectura completa de flash.
- Escape al conectar llegó al ISP con Bootmagic de la aplicación deshabilitado.
  No se ensayó una aplicación deliberadamente corrupta ni se garantiza que sea
  imposible bloquear el teclado. No hay backup OEM propio ni restauración OEM
  comprobada. El encapsulado/SKU exacto del MCU y la revisión de PCB siguen
  inferidos; el protocolo de la unidad sí confirmó familia SN32F26x y CS0.
- 107 tests automatizados pasan en macOS, además de la prueba humana indicada.
  Los tests simulados no equivalen a cortes de alimentación o desgaste reales.

La evidencia detallada está en `hardware/first-flash-evidence.json`. El usuario
restauró las tres posiciones a transparentes desde GUI tras otro Unlock. Después
de reconectar, los 896 bytes coincidieron con el mapa inicial: cero diferencias
y estado bloqueado. No quedaron asignaciones de prueba.

## Uso diario y configuración

Cada asignación admitida se guarda automáticamente en el teclado. No hay una
compilación C o grabación final obligatoria al terminar el mapa. Se puede cerrar
Vial, desconectar y usarlo en otra máquina conservando las asignaciones.

Para editar tras encender o reconectar:

1. Abrir un solo cliente Vial y seleccionar el HyperX.
2. En macOS, usar **Security → Unlock en la barra de menús superior**.
3. Mantener **Tab + Caps Lock físicos** hasta completar la barra (unos cuatro
   segundos con el GUI de referencia); después soltar.
4. Elegir la capa y la tecla destino del dibujo superior. Elegir luego la
   asignación en el selector inferior. Es una operación con clics, no escribir
   con la tecla física para asignarla.

Tab+Caps por sí solo no abre el desbloqueo. Desbloquear no cambia la protección
MCU/CS0 ni desprotege flash. Para usar el mapa no hace falta desbloquear ni tener
Vial abierto. `▽` / `KC_TRNS` es transparente, no deshabilitado (`KC_NO`).

No abrir simultáneamente la app, la web y las herramientas RAW. Hubo timeouts
que se despejaron al cerrar clientes y reconectar; la causa no se aisló y no se
considera resuelta la fiabilidad general. Los scripts no reintentan escrituras
si una respuesta falta o es inválida.

## Qué admite la variante actual

| Función | Estado y alcance |
| --- | --- |
| Letras, números, símbolos básicos, navegación y F-keys | Admitidos y editables; no se han probado exhaustivamente todos los códigos/posiciones. |
| Modificadores y combinaciones con modificadores | Admitidos por la política del firmware. |
| Mod-tap y layer-tap | Admitidos; layer-tap limitado a capas 0–3. Tiempo de tapping compilado, no ajustable desde QMK Settings de Vial. |
| MO, TO y TG | Admitidos para capas 0–3; Fn de base usa MO(1). Fn+A se probó realmente. |
| Transparentes | Admitidas; heredan de la capa inferior. |
| Macros, combos y tap-dance dinámicos | No implementados. |
| One-shot, multimedia/volumen, mouse keys y MIDI | No admitidos por el protocolo actual. |
| QMK Settings, encoders y comandos de reset/bootloader desde Vial | No implementados o rechazados deliberadamente. |
| Retroiluminación y efectos | Sin soporte en este firmware. |

Que la GUI muestre una función no significa que este firmware la admita. Vial
puede mostrar optimistamente un cambio cuyo SET fue rechazado: no confiar solo
en el dibujo. La whitelist de códigos está en `vial_editable/keymap.c`.
Las pruebas reales hasta ahora cubren casos concretos, no toda la tabla.

## Retroiluminación: desactivada, no una avería nueva demostrada

Sí: con este firmware no se conserva el control de retroiluminación OEM.
`BACKLIGHT_ENABLE`, `RGBLIGHT_ENABLE`, `RGB_MATRIX_ENABLE` y `LED_MATRIX_ENABLE`
están deshabilitados. No hay un controlador de iluminación validado para este
port. Esto no demuestra daño físico en los LEDs.

Recuperarla exige identificar y validar su control sin abrir la carcasa,
implementar el controlador adecuado y comprobar el presupuesto y el efecto
sobre escaneo/USB. No basta activar una casilla de Vial ni cambiar un flag.
No se promete que pueda recuperarse con las restricciones y evidencias actuales.

## Memoria y por qué cuatro capas

Presupuesto del candidato realmente compilado; las pilas son reservas, no
máximos medidos en ejecución:

| Recurso | Uso actual |
| --- | ---: |
| Aplicación ARM | 21 412 B de flash |
| Imagen de actualización con padding | 21 440 B |
| Capacidad de aplicación antes de los bancos actuales | 28 160 B, desde 0x200 hasta 0x7000 |
| Margen de aplicación, descontada la imagen con padding | 6 720 B; es flash, no RAM |
| RAM del modelo de plataforma | 2 048 B |
| Reserva estática hasta el heap, incluidas pilas/alineación | 1 968 B |
| Heap restante | 80 B |
| Pilas IRQ / proceso reservadas | 224 B / 480 B |
| Mapa de cuatro capas en formato de protocolo | 896 B, guardados en flash, no duplicados como mapa RAM |
| Almacenamiento persistente reservado | Dos bancos de 1 024 B: mapa más cabecera/commit |

Los 80 B de heap NO son una medida del margen de pila. Falta medir high-water
real antes de afirmar que otra función es segura por haber enlazado. El Raw HID
upstream original excedía los 2 KB incluso sin Vial completo; por eso se hizo un
transporte compacto y se seleccionaron funciones, no simplemente se habilitó
VIAL_ENABLE. La flash disponible no resuelve un overflow de RAM.

**Cuatro capas es el límite de esta variante, no un límite universal de Vial.**
[La documentación oficial](https://get.vial.today/manual/layers.html) explica que
el número se configura al compilar, no desde la GUI. Aquí cada capa de matriz
14×8 ocupa 224 B: cuatro son 896 B. Con 128 B de cabecera/commit completan el
banco de 1 024 B. También parser, validadores y mapas están limitados a 0–3.

Agregar capas exige cambiar el formato/reserva o compactar las posiciones,
versionar y migrar los mapas existentes, actualizar límites y probar recuperación
ante fallos. Podría investigarse sin asumir un gran aumento de RAM, porque el
mapa vive en flash. No se garantiza todavía un número mayor concreto ni se deben
copiar rangos virtuales o adivinados a una orden de programación.

## Comparación con el flujo del Silakka54

Para **seleccionar teclas, organizar capas y conservar cambios con Vial**, ya
existe el mismo tipo de flujo básico. Puede usarse una zona de 42 teclas del
HyperX sin desactivar las demás posiciones sanas.

No es equivalente al catálogo completo de funciones de un firmware Vial-QMK.
La referencia pública ofrecida del Silakka incluye one-shot y multimedia/volumen
que esta variante aún no admite. No se leyó ni modificó el Silakka físico.
El mapa exacto tampoco se ha importado: son matrices y distribuciones diferentes.

Hay margen para mejoras selectivas, no evidencia para prometer paridad total.
Los candidatos a evaluar son one-shot y multimedia necesarios para ese flujo,
seguido de otras funciones o más capas según prioridad. Cada mejora debe medir
flash, RAM/pilas y latencia; no activar todo a la vez ni asumir que C hace caber
cualquier función. Una asignación ordinaria admitida NO requiere reflasheo.

## Qué falta y qué no debe confundirse con una función terminada

- Restauración de A/S/D completada; mantener una base limpia al cerrar futuras pruebas.
- Configurar el mapa ergonómico deseado en Vial y comprobar las funciones usadas;
  acordar sustitutos para cualquier código no admitido antes de importaciones.
- Medir pilas, fiabilidad USB/reconexión, teclas simultáneas, rebote y matriz
  completa; no se declara firmware estable por una prueba de remapeo.
- Evaluar desgaste y latencia de escrituras: cada cambio distinto reemplaza 17
  páginas. No-op no escribe. Mínimo documentado de 10k ciclos, no prometer vida
  ilimitada ni usar cambios de configuración continuos como animación.
- Evaluar por separado nuevas funciones y el controlador de iluminación.
- Mantener pendientes OEM, revisión exacta y recuperación de app corrupta.
  El checklist general sigue saliendo con código 2 por esas evidencias; no es un
  mecanismo de autorización ni deshace los hitos de hardware ya verificados.

## Qué respalda GitHub

GitHub conserva el historial de fuentes, scripts, tests y evidencia pública
saneada que se confirme y envíe. No es un backup del contenido OEM de esta unidad
ni copia automáticamente lo ignorado: toolchain, binarios compilados, updater,
DLL, fotos, logs privados, `tmp/` y snapshots locales de mapas quedan fuera.

Los hashes y revisiones fijadas ayudan a reconstruir candidatos; no sustituyen
preservar de forma privada los artefactos necesarios ni verificar su procedencia.
No se publican binarios propietarios, credenciales ni datos de la etiqueta.

## Cambio visual posterior

Se añadieron al dibujo las cinco posiciones omitidas inicialmente. No se cambió
la matriz, UID, código de escaneo, whitelist, formato o contenido del mapa.
La definición XZ sigue ocupando416 B y la aplicación21412 B; RAM1968 B sin variar.
Lectura real de la definición:87 coordenadas únicas; los896 B del mapa siguen
idénticos a la base restaurada y las cinco posiciones continúan en 0 en las 4 capas.
Dibujarlas no equivale a habilitarlas ni a reparar la avería.
