# HyperX Alloy FPS Pro: viabilidad de firmware propio

**Estado al 2026-10-29:** QMK compilado con cuatro capas; variante `custom42_fn`
con 42 posiciones + F1–F12. **Primer ciclo USB OEM → ISP → OEM comprobado en la
unidad**, familia SN32F26x y seguridad CS0 reportadas; usuario confirmó que sigue
escribiendo. Jumploader propio compilado (436 B), **no instalado ni validado**.
**50 pruebas pasan en Linux/macOS; todavía sin flasheo ni Vial completo.** No hay backup
propio ni recuperación demostrada ante una aplicación inválida.

**Nuevo código:** [prototipo Vial de solo lectura](docs/vial-readonly-prototype.md)
compilado para ARM:19460 B flash,1952/2048 B RAM, cuatro capas y tapping
conservados. Identidad, definición y lectura de mapas comprobadas en host;
**sin edición persistente ni detección real en Vial**.

**Novedades y continuación:** [informe USB/arranque e instalación pendiente](docs/usb-isp-and-startup.md).
Los informes anteriores conservan contexto histórico; la limitación USB del
entorno anterior quedó superada al trabajar por SSH.

## Un solo proyecto, varios archivos

Esta carpeta reúne el trabajo original por SSH y todos los avances posteriores.
No son proyectos distintos: `firmware/` contiene C/ASM y mapas; `scripts/` las
herramientas; `tests/` sus pruebas; `hardware/`, `toolchains/` y `docs/` las
evidencias y documentación. Este README es el punto de entrada único.

En esta continuación, la copia macOS accesible por SSH es la fuente principal
de edición. La máquina Linux local aporta el toolchain y allí está conectado
el HyperX, según aclaró el usuario. Los roles de las máquinas cambiaron respecto
a la etapa SSH anterior; no copiar sus supuestos de ubicación. No
editar ambos árboles independientemente: comparar cambios antes de sincronizar,
sin borrados automáticos; cuando exista el remoto GitHub, usar el mismo repo.
No hay sincronización automática ni publicación realizada.

Los builds, referencias privadas y dependencias se conservan en `build/` y
`artifacts/`, respetando `.gitignore`: no se sube la carpeta completa a GitHub.
El toolchain importado es Linux x86_64, no ejecutable nativo de macOS. Las
pruebas Python pueden ejecutarse localmente; los builds ARM siguen en Linux.

**Vial y memoria:** [mediciones Raw HID, iluminación y alternativa de tres capas](docs/vial-memory-budget.md).

## Seguimiento del proyecto

- **Empezar aquí:** [qué se logró, qué significa el arranque auxiliar y cómo seguir sin abrir el teclado](docs/next-steps.md).
- [Objetivo y reglas para futuras sesiones/agentes](AGENTS.md).
- [Revisión antes de publicar en GitHub](docs/publication-review.md).
- [Identificación del hardware y evidencia fotográfica](docs/hardware-identification.md).
- [Plan de respaldo, recuperación y selección de base QMK](docs/backup-and-recovery.md).
- [Bitácora de avances y pendientes](docs/project-log.md).
- [Desarrollo sin abrir la carcasa: extracción y matriz reconstruida](docs/closed-case-development.md).
- [Código del firmware y pruebas](firmware/README.md).
- [Build ARM, memoria y requisito de arranque en 0x200](docs/arm-build-and-boot.md).

Se documentará cada avance diferenciando lo observado, lo inferido y lo pendiente. No se incorporó la foto original al proyecto porque muestra identificadores de la unidad.

## Objetivo y límites

- Reutilizar el **HyperX Alloy FPS Pro** con aproximadamente 42 posiciones activas y capas que reproduzcan, en lo posible, el flujo de trabajo del usuario en su Silakka54.
- **No modificar, flashear, reconfigurar ni capturar entradas del Silakka54**. Su configuración actual queda fuera del proyecto.
- **No abrir el HyperX**: el usuario rechazó el desmontaje y autorizó continuar con inferencia, firmware de distribución y una ruta por USB. No volver a pedir fotos internas.
- El usuario reporta que no funcionan cinco teclas, desde `8` hasta `=/+`, y que Backspace sí funciona. Confirmar leyendas/distribución física antes de mapearlas.
- Se leyeron metadatos y fuentes y se realizó una consulta ISP acotada mediante hidraw únicamente sobre el HyperX, con retorno OEM confirmado. No se leyeron entradas de teclas ni se ejecutaron actualizadores. Capstone, SonixQMK y el compilador ARM están aislados dentro del proyecto; no se instalaron herramientas globalmente ni servicios.

## Conclusión provisional

**El objetivo funcional —capas sobre unas 42 teclas sanas— es viable por varias vías. Ya se compiló QMK con cuatro capas y una matriz inferida 14 × 8: `custom42` ocupa 17316 B y `default` 16868 B. Ambos caben estáticamente en el MCU candidato, pero no se probaron en esta unidad. Existe ahora un prototipo de lectura del protocolo Vial; el remapeo Vial nativo completo no está integrado ni garantizado.**

El [informe ARM](docs/arm-build-and-boot.md) detalla el límite actual: aplicación enlazada en `0x200` con dependencia de un arranque auxiliar, recuperación sin verificar y solo 88 B de heap tras reservar pilas y datos en 2 KB de RAM. No es una medida de margen de pila en ejecución. Por SSH ya se consultó el ISP, pero no se probó el firmware nuevo.

No hace falta reconstruir una copia exacta del firmware propietario: el camino preferible, si el hardware lo permite, es portar una base abierta que reemplace sus funciones. La ingeniería inversa se limitaría al hardware y a los aspectos de actualización/recuperación que realmente hagan falta.

## 1. Identidad observada del teclado conectado

Lectura de `/sys/bus/usb/devices/1-6` durante esta sesión:

| Campo | Valor observado |
| --- | --- |
| Fabricante | `Kingston` |
| Producto | `HyperX Alloy FPS Pro Mechanical Gaming Keyboard` |
| USB VID:PID | `0951:16d2` |
| `bcdDevice` | `2112` |
| USB | 2.00; 12 Mb/s (full-speed) |
| Interfaces | 3 HID |

La ruta `1-6` puede cambiar al reconectar. Los identificadores USB no revelan el microcontrolador ni la revisión de PCB. `bcdDevice=2112` no demuestra por sí solo la versión exacta del firmware instalado. No se registraron números de serie.

La fotografía inferior aportada después confirma **Alloy FPS Pro, SKU `HX-KB4RD1-US`**, referencia de etiqueta `3500241-001.A02LF` y alimentación nominal `5 V CC / 500 mA`. La referencia `A02LF` no se tratará como revisión de PCB sin verificar la serigrafía interna. El MCU sigue sin confirmarse físicamente.

Históricamente `lsusb` falló en el entorno inicial; la sesión SSH posterior sí dispone de nodos USB y permitió la consulta ISP documentada.

## 2. Microcontrolador candidato y antecedentes

- Un [desmontaje de primera mano de TweakTown](https://www.tweaktown.com/reviews/8405/hyperx-alloy-fps-pro-mechanical-gaming-keyboard-review/index.html#Inside-the-Alloy-FPS-Pro) identifica **Sonix SN32F268FG**, ARM Cortex-M0, 48 MHz, en la unidad reseñada. **No confirma el chip de la unidad del usuario**.
- [SonixQMK](https://sonixqmk.github.io/SonixDocs/) documenta soporte para SN32F268. El código actual también incluye un [ejemplo mínimo SN32F260 con procesador SN32F268F](https://github.com/SonixQMK/qmk_firmware/blob/62973ee48a976c6f7cc6d4f7b198bd48a2fdfe60/keyboards/handwired/onekey/sn32f260/keyboard.json).
- La [guía oficial de productos SONiX](https://www.sonix.com.tw/download/MCU.pdf) y la [hoja de datos SN32F260](https://www.sonix.com.tw/files/1/19A84D2F7217D8B4E060007F0100686A) especifican **32 KB de flash total, 2 KB de RAM de usuario y 256 B de FIFO USB**. La hoja de datos reserva 2 KB de la flash al bootloader.
- SonixQMK advierte que [cada placa requiere mapear su matriz y periféricos](https://sonixqmk.github.io/SonixDocs/faq/), aunque comparta chip con otra.

### Búsqueda acotada de un port existente

Se consultó el árbol recursivo completo, no truncado, de `SonixQMK/qmk_firmware`, rama `sn32_develop`, SHA `62973ee48a976c6f7cc6d4f7b198bd48a2fdfe60`:

- Bajo [`keyboards/hyperx`](https://github.com/SonixQMK/qmk_firmware/tree/62973ee48a976c6f7cc6d4f7b198bd48a2fdfe60/keyboards/hyperx) aparece `alloy_origins_core`, **no un port del FPS Pro**.
- La búsqueda de issues/PRs con `alloy` en ese repositorio devolvió [PR #394: Alloy Origins Core](https://github.com/SonixQMK/qmk_firmware/pull/394), otro modelo.
- Las búsquedas públicas adicionales por nombre/modelo no permitieron identificar un port listo del FPS Pro. Esto **no demuestra que nadie lo haya intentado** ni cubre trabajo privado o conversaciones de Discord.
- El árbol completo de `vial-kb/vial-qmk`, rama `vial`, SHA `dd43959ae5c08d8a28d38a1acf7b04e86b14a344`, no mostró rutas HyperX ni SN32F260 por nombre. No se verificó una integración Vial/Sonix utilizable para este teclado.

**No usar un binario del Origins Core, de otro HyperX ni de otro teclado con el mismo chip.** Los pines, la matriz, los LEDs y el mecanismo de arranque pueden ser distintos.

## 3. Vial no es solo un archivo de distribución

[Vial requiere firmware compatible](https://get.vial.today/docs/porting-to-vial.html), no basta con instalar la aplicación ni cargar un JSON sobre el firmware de fábrica.

El presupuesto de memoria del MCU candidato es pequeño. La [documentación de tamaño de Vial](https://get.vial.today/docs/firmware-size.html) contempla reducir capas dinámicas, macros, combos, tap dance y otras funciones por límites de flash, RAM y almacenamiento persistente.

Hipótesis a evaluar, no resultado demostrado:

1. QMK mínimo con matriz, USB, debounce y capas definidas al compilar.
2. Medir flash, RAM estática y margen de pila; comprobar almacenamiento persistente seguro si se busca configuración dinámica.
3. Evaluar VIA/Vial como una fase adicional de integración, posiblemente con funciones reducidas.

Usar solo 42 posiciones puede ahorrar parte del mapa, pero no elimina el coste de la pila USB, el sistema base ni las funciones dinámicas. No se promete iluminación, macros avanzadas o Vial completo.

## 4. Las cinco teclas averiadas

Existe un [reporte comunitario de primera mano con el mismo grupo `8, 9, 0, -, =`](https://www.reddit.com/r/HyperX/comments/1pmtkk8/fix_hyperx_alloy_fps_pro_dead_keys_8_9_0_fixed_by/). Su autor describe una pista de matriz interrumpida y una reparación mediante un puente.

**Inferencia:** conviene investigar una conexión común de matriz antes de asumir cinco switches rotos o un fallo de firmware. No es un diagnóstico de esta unidad y no se deben copiar puntos de soldadura del reporte sin verificar revisión y continuidad de su PCB, con el teclado desconectado.

Una pista abierta, un diodo o un switch dañado no se repara cambiando firmware. Si el resto de la matriz es estable, se pueden omitir esas posiciones y colocar números/símbolos en capas de teclas sanas. La reparación es una línea opcional, separada del objetivo de capas.

## 5. Caminos posibles

| Camino | Qué ofrece | Condiciones y límites |
| --- | --- | --- |
| Port QMK en MCU original | Capas dentro del teclado, sin software del PC durante el uso | Confirmar chip/revisión, mapear matriz, comprobar memoria y vía de recuperación. Riesgo de dejarlo sin funcionar al flashear. Vial es trabajo adicional, no garantizado. |
| Prototipo por software, solo HyperX | Probar distribución, capas y tap/hold sin reemplazar firmware | Por ejemplo, [Kanata en Linux permite seleccionar dispositivos exactos](https://jtroo.github.io/config.html#linux-only-linux-dev). Debe usar una selección explícita del HyperX; nunca autodetección global que intercepte el Silakka54. Depende del PC y no es QMK/Vial nativo. No está instalado ni activado por este proyecto. |
| Adaptador USB programable externo | Capas portátiles sin modificar internamente el HyperX | [HID Remapper](https://github.com/jfedor2/hid-remapper) tiene [capas y tap/hold](https://www.remapper.org/manual/). Usa su propia interfaz, no Vial/QMK. Requiere hardware host USB y validar compatibilidad con los reportes del HyperX. No se probó. |
| Sustituir controlador o recablear | Ruta alternativa a QMK/Vial con un MCU soportado y más recursos | Inferencia de diseño: exige trabajo electrónico, identificar/aislar el controlador original, verificar niveles eléctricos y mapear la matriz. No conectar otro MCU en paralelo a ciegas. |

El [conversor USB-USB incluido en Vial-QMK](https://github.com/vial-kb/vial-qmk/tree/dd43959ae5c08d8a28d38a1acf7b04e86b14a344/keyboards/converter/usb_usb) es otro antecedente, **no un producto Vial listo para este caso**: su README limita la entrada al protocolo HID Boot (6KRO), no NKRO genérico. Necesitaría validación y adaptación propias.

## 6. Adaptación desde el Silakka54

- Se pueden trasladar funciones a unas 42 posiciones sanas, números/símbolos a capas y navegación a una capa específica.
- La selección concreta de teclas, capas y tiempos queda pendiente: no se leyó la configuración del Silakka54.
- Se puede trabajar desde una copia de configuración que el usuario ya tenga, o desde una descripción de sus capas, sin interactuar con ese teclado.
- No se puede reproducir por firmware la separación física, el escalonado por columnas ni el conjunto de teclas independientes de pulgar. Una barra espaciadora con un solo switch no se convierte en varios botones independientes.
- En rutas externas/por software solo son asignables entradas que el firmware original efectivamente envíe; no asumir que `Fn` se transmite al host.

## 7. Próximos pasos y condiciones antes de flashear

1. Mantener cerrada la carcasa. La identificación física opcional propuesta antes fue rechazada; continuar con evidencia de distribución y validación cerrada por USB cuando sea accesible.
2. Contrastar la imagen y revisión sin desproteger ni borrar: el descriptor extraído coincide en VID/PID y bcdDevice, pero no demuestra identidad byte a byte de la unidad.
3. La matriz se reconstruyó estáticamente; falta validar el comportamiento y la dirección eléctrica en esta revisión. No activar LEDs aún no estudiados.
4. Completar el [plan de respaldo y recuperación](docs/backup-and-recovery.md). El paquete del espejo no es un dump propio ni garantiza restauración. **No desbloquear para copiar**.
5. El build QMK/ARM y la comprobación estática de flash/RAM están completados. Falta comprobar máximos de pila y estabilidad en ejecución; las pruebas del anfitrión no sustituyen esa validación.
6. Validar el jumploader requerido, entrada/salida y recuperación del bootloader antes de escribir. No escribir el `.bin` desde cero ni conservar a ciegas los vectores OEM. No borrar/sustituir el bootloader como primer experimento.
7. Probar luego las capas provisionales; evaluar Vial solo con una base funcional y memoria/persistencia comprobadas.

**El usuario autorizó avanzar con cuidado; esa autorización no sustituye validación técnica. No se flasheará el port con recuperación/geometría sin verificar. `scripts/check_port_readiness.py` informa los pendientes; no realiza operaciones sobre el teclado.**
