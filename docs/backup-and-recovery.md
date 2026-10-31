# Respaldo y recuperación antes del port

> [!NOTE]
> Informe de una fase anterior, conservado por su evidencia y fuentes. No usar
> sus estados provisionales como estado actual ni sus comandos como receta universal.
> Leer primero [README](../README.md), [estado](status-and-limits.md) y
> [seguridad/recuperación](safety-and-recovery.md).

Actualizado: 2026-10-30.

**Prioridad del ensayo:** evaluar una primera prueba con recuperación mínima
para cargar otro candidato, sin exigir restauración OEM perfecta. Ver
[el criterio actualizado](first-trial-planning-history.md).
Los requisitos de preservar el ISP, conocer protocolo/rangos y mantener la
carcasa cerrada siguen vigentes. Esto cambia el alcance buscado, no la evidencia:
ni el rescate de una app fallida ni la restauración OEM están aún comprobados.

**Resultado de esa fase: se obtuvo un paquete desde un espejo comunitario y se extrajo su imagen estáticamente. No está autenticado contra el fabricante, no es un volcado de la unidad y no se ha probado restauración. No existe todavía un backup propio del teclado.** La investigación se limita a carcasa cerrada; las propuestas anteriores de inspección física quedaron descartadas. Ver [avance de extracción](closed-case-development.md).

## 1. Tres cosas distintas

| Elemento | Qué conserva | Estado |
| --- | --- | --- |
| Registro de identificación | Modelo, etiqueta y metadatos USB | Documentado en [hardware-identification.md](hardware-identification.md). No es una copia de firmware. |
| Paquete de distribución | Una versión distribuida del firmware y/o su actualizador | ZIP obtenido de `IRus/blog`, espejo no autenticado. Imagen HEX extraída con checksums válidos, nombre/USB consistentes; procedencia oficial y recuperación pendientes. No representa necesariamente el contenido actual de esta unidad. |
| Volcado de la unidad | Bytes realmente leídos de las regiones identificadas del chip | No obtenido. Método de lectura y protección desconocidos. Aplicación, bootloader, opciones de seguridad y configuración persistente pueden ocupar regiones distintas. |

Guardar el actualizador oficial es útil como material de recuperación, pero no equivale a haber copiado el teclado. Tener un archivo tampoco demuestra que se pueda restaurar después de un fallo.

## 2. Advertencia crítica: no quitar protección para copiar

Para el **SN32F260/SN32F268 candidato**, la [hoja de datos SONiX v2.1, §11.9, página impresa 127](https://www.sonix.com.tw/download/file?b4f85bbf38a24e969c93a0bc6bc0110e=) establece que pasar la protección de lectura de activada a desactivada provoca un **borrado masivo de User ROM**. El §11.10 aclara que un checksum puede seguir siendo consultable con lectura protegida.

Por tanto:

- No ejecutar `unlock`, `unprotect`, `mass erase`, cambios de Code Security ni acciones equivalentes para conseguir un respaldo.
- Un checksum no permite reconstruir el contenido ni es un backup restaurable.
- No afirmar que la unidad está protegida: todavía no se ha identificado físicamente su MCU ni leído su estado.
- Si el contenido no se puede leer sin destruirlo, detener esa vía y documentar la limitación. Conseguir una imagen original externa sería una alternativa, no un volcado propio.

## 3. Localización de material oficial

En una [respuesta de soporte HyperX de 2023](https://www.reddit.com/r/HyperX/comments/12oe9ke/hyperx_alloy_fps_pro_firmware/), la cuenta `HyperxGaming` proporciona el enlace corto `https://hyperx.gg/3n3EnUa` al actualizador independiente del FPS Pro y lo identifica como oficial en ese momento.

En la primera búsqueda no se pudo resolver ese enlace con la herramienta web; la consulta HTTP local falló por resolución de nombre. Después se encontró el ZIP conservado en un repositorio comunitario y se extrajo sin ejecutarlo. El fabricante sigue sin autenticar esa copia y no se ha demostrado su recuperación en esta revisión.

Secuencia pendiente:

1. Resolver una fuente del fabricante o pedir a soporte el paquete correspondiente al SKU y revisión confirmados.
2. Descargarlo **sin ejecutarlo**. Registrar URL final, procedencia, fecha, tamaño y SHA-256. El hash fija la identidad del archivo; por sí solo no certifica su autenticidad.
3. Inspeccionar el archivo estáticamente: contenido del contenedor, firma del ejecutable si existe, identificación de modelos, versión, imágenes y límites de escritura. Si hay firmware extraíble, conservar el original y registrar también los hashes de las imágenes extraídas.
4. Contrastar MCU, tamaño, mapa, offset de aplicación y mecanismo de arranque con la unidad real. `bcdDevice=2112` es solo una pista, no una prueba de igualdad con una versión de distribución.
5. Documentar qué recupera y qué no: aplicación, bootloader y/o ajustes. No etiquetarlo como copia íntegra si no lo es.

Los ejecutables y binarios originales que se obtengan se mantendrán como material de análisis; no asumir autorización para redistribuirlos públicamente.

## 4. Evaluación de un volcado no destructivo

El [README de SonixFlasherC revisado al commit `73f9fab8a82c5c4f91181d276676c8f936726925`](https://github.com/SonixQMK/SonixFlasherC/blob/73f9fab8a82c5c4f91181d276676c8f936726925/README.md) documenta escritura, reinicios e información/checksum. **No documenta un comando de volcado completo**. Esto limita lo que podemos prometer con esa herramienta, no demuestra que toda lectura por cualquier vía sea imposible.

No se compiló ni ejecutó SonixFlasherC contra el hardware. Consultar información mediante una herramienta de flasheo también puede implicar tráfico al dispositivo o un cambio de modo: no se hará como sustituto de una lectura pasiva.

Para evaluar una lectura real:

1. Inferir MCU/revisión con imagen de distribución y protocolo/USB, sin abrir la carcasa. Registrar explícitamente la confianza y lo que no pueda confirmarse.
2. Establecer si hay lectura USB soportada o si haría falta un depurador compatible y acceso físico. Tener pines SWD no garantiza que la flash sea legible.
3. Revisar el procedimiento para asegurar que no borra, desbloquea, escribe opciones, programa una aplicación auxiliar ni restaura valores de fábrica. No adivinar tensiones o pines de conexión.
4. Solo tras acordar una intervención concreta y no destructiva, leer las regiones autorizadas. Seleccionar exclusivamente el HyperX previsto, sin acceder a otros dispositivos.
5. Para regiones estáticas, obtener dos lecturas independientes y comprobar identidad de bytes/hashes. Conservar mapa de direcciones, tamaño, método, herramienta/versión y cobertura exacta. Dos lecturas iguales ayudan a verificar consistencia, no prueban restaurabilidad.

Si alguna región no es legible, el respaldo será parcial y se identificará como tal. No crear un archivo vacío o rellenado para presentarlo como backup.

## 5. Condiciones antes de un primer flasheo

- Evidencia suficiente que vincule MCU/revisión inferidos con la unidad, sin depender solo de otro teclado o de su aspecto.
- Matriz y periféricos relevantes mapeados; pines no identificados no se activan a ciegas.
- Material original recuperable y sus límites documentados, o aceptación explícita del riesgo residual sin respaldo completo.
- Procedimiento de recuperación aplicable a esa revisión, con alcance y limitaciones claros; no prometer que el bootloader es indestructible.
- Geometría de flash y rangos de escritura comprobados; no borrar ni sustituir el bootloader como primer experimento.
- Validar el jumploader requerido por el candidato SonixQMK: su aplicación está enlazada en `0x200`, mientras la imagen OEM tiene vectores en cero. Ni escribir el `.bin` desde cero ni preservar sin más los primeros 512 B OEM es una transición demostrada. Ver [análisis de arranque](arm-build-and-boot.md).
- Firmware mínimo compilado y revisado, incluidos flash, RAM y margen de pila.
- La autorización para desarrollar firmware no incluye un desbloqueo destructivo ni imágenes con rangos de escritura adivinados. Mantener las validaciones antes de cualquier escritura.

No es necesario reflashear el firmware original simplemente para guardar su paquete. Una prueba de restauración sería una intervención separada, no una lectura inocua.

## 6. Qué reutilizar de otro teclado QMK/Vial

Para reutilizar código existente, **el criterio principal es la electrónica, no tener el mismo número o dibujo de teclas**.

| Parte reutilizable | Condición |
| --- | --- |
| Plataforma, arranque y controlador USB | MCU exacto soportado y configuración compatible con este chip/bootloader. |
| Escaneo de matriz | Adaptarlo a las filas, columnas, pines y diodos reales del HyperX. Dos teclados TKL pueden cablearse de maneras distintas. |
| Definición visual y distribución | Un TKL similar puede servir como plantilla de representación, nunca como prueba del pinout. |
| Distribución y funciones deseadas | Trasladarlas a teclas sanas cuando exista un escaneo fiable. Se puede conservar el mapa de las teclas físicamente presentes y utilizar solo 42. |
| Vial y almacenamiento dinámico | Integración adicional con presupuesto de flash/RAM/persistencia verificado. No queda habilitado por copiar un JSON. |

Si se confirma el Sonix candidato, el [ejemplo mínimo `handwired/onekey/sn32f260`](https://github.com/SonixQMK/qmk_firmware/tree/62973ee48a976c6f7cc6d4f7b198bd48a2fdfe60/keyboards/handwired/onekey/sn32f260) es una referencia de plataforma a estudiar, **no un firmware listo para flashear al HyperX**. No se han aprobado sus pines ni su configuración de arranque para esta placa. [SonixQMK explica por qué hay que mapear cada placa](https://sonixqmk.github.io/SonixDocs/faq/).

Orden propuesto: **identificación → material original / viabilidad del volcado → recuperación → matriz y port mínimo → capas → evaluación de Vial**. Se puede analizar/compilar código sin modificar el teclado; el punto de no retorno es la intervención física o escritura, no editar un proyecto de firmware.
