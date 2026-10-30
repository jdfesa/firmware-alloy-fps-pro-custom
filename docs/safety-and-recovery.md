# Seguridad, recuperación y ausencia de backup OEM

> [!WARNING]
> **Este procedimiento se usa bajo la responsabilidad de quien lo ejecuta.
> Puede dejar un teclado inutilizable. No existe una restauración OEM comprobada
> ni una garantía de recuperación para otra unidad o revisión.**

El éxito documentado corresponde a un HyperX Alloy FPS Pro HX-KB4RD1-US. La
revisión exacta de PCB y el encapsulado MCU no se verificaron físicamente. Un
VID/PID, nombre o SKU coincidente no basta para copiar el procedimiento.

## Cuatro cosas que no son equivalentes

| Recurso | Lo que realmente tenemos |
| --- | --- |
| Historial de fuentes | Git y GitHub; no son bytes leídos del teclado. |
| Snapshot del mapa | Lectura de 896 B de configuración, privada; no incluye OEM, arranque ni opciones del chip. |
| Entrada de rescate | Jumploader instalado, Escape al conectar y consultas ISP comprobadas en esta unidad. |
| Backup/restauración OEM | **No obtenidos ni probados.** La imagen extraída de un paquete de referencia no es un dump de la unidad ni está autenticada/restaurada. |

No denominar al jumploader un «backup mínimo». Permite intentar volver a cargar
otra aplicación mientras responda el ISP; no reconstruye el OEM ni elimina el
riesgo de que falle el propio arranque.

## Qué se comprobó del rescate

El arranque auxiliar examina Escape antes de entrar a la aplicación. Al conectar
manteniéndola, el teclado enumeró en ISP y respondió F260/CS0. La variante
editable tenía Bootmagic de aplicación deshabilitado, por lo que esa comprobación
no dependía de la ruta duplicada de QMK. Las actualizaciones posteriores se
limitaron a la app desde 0x200, fuera de arranque y bancos del mapa.

No se probó una aplicación deliberadamente corrupta, un corte mientras se escribe
el arranque ni todas las formas de fallo. La primera instalación del jumploader
fue el punto de mayor riesgo. El ACK/eco final no equivale a un volcado completo.
Si se pierde la entrada de rescate, no hay una recuperación comprobada compatible
con la carcasa cerrada. No afirmar por ello que sea físicamente irreparable;
simplemente no existe aquí una vía validada bajo las restricciones del proyecto.

## Cuándo entrar con Escape y cuándo no

Escape al conectar solicita el ISP desde el jumploader, antes de la aplicación.
Se usó para instalar candidatos app-only y comprobar el rescate. No inicia una
programación automáticamente. En ese modo no se espera escribir normalmente ni
que Vial detecte el configurador de la app.

No usar Escape para editar mapas ni como rutina cada vez que se abre Vial.
Para eso se arranca sin Escape y luego se usa Security→Unlock con Tab+Caps.
Durante una prueba, mantener Escape hasta observar el ISP e indicar cuándo
soltar. Si se entró accidentalmente y no hay una escritura en curso, reconectar
sin Escape permite intentar volver a la app. Nunca hacerlo durante programación.

## Qué hacer ante una eventualidad

- **El teclado escribe, pero no guarda asignaciones:** repetir Security → Unlock;
  un bloqueo de edición no es un brick. Leer [uso](usage.md).
- **Vial no responde:** cerrar clientes por completo y reconectar sin Escape.
  Verificar solo la identidad del HyperX; no consultar otros teclados.
- **La aplicación no arranca:** se puede comprobar la entrada ya observada en
  esta unidad: desconectar solo HyperX, mantener Escape al conectar y consultar
  metadatos ISP. Mantener hasta observarlo; indicar expresamente cuándo soltar.
  No enviar programación solo porque apareció un dispositivo.
- **ISP responde:** conservarlo mientras se revisan protocolo, CS0, checksum,
  fuentes, manifiesto, hash y rango del candidato. Una actualización app-only
  revisada puede ser viable; no prometerla si cambió el arranque o la identidad.
- **Falla una escritura:** detener sin reintentar ni reiniciar automáticamente.
  Conservar logs privados y el estado ISP si sigue accesible. No desconectar
  durante una programación en curso.
- **ISP no aparece o la identidad es distinta:** detenerse. No borrar, quitar
  protección, usar otra herramienta a ciegas ni abrir el teclado para seguir
  estas instrucciones. Documentar el límite y buscar evidencia compatible.

## Qué no hacer

- No ejecutar el updater propietario ni su DLL: se analizaron estáticamente.
- No usar unlock/unprotect, cambios de Code Security ni mass erase para leer un
  backup. La desprotección del MCU candidato puede borrar User ROM.
- No confundir ese unlock del MCU con el desbloqueo de edición Tab+Caps de Vial.
- No instalar un binario de Origins Core, otro teclado o un chip parecido.
- No escribir la app enlazada en 0x200 desde cero; tampoco instalar el jumploader
  solo encima del OEM enlazado en cero ni conservar sus vectores a ciegas.
- No escribir en direcciones deducidas del tamaño de un archivo o de un banco
  virtual de tests. Los límites requieren manual/protocolo y evidencia.
- No abrir, soldar o manipular internamente el HyperX; no tocar el Silakka54.
- No marcar validaciones como verdaderas por conveniencia o aceptación del riesgo.

## ¿Se puede volver al estado de fábrica?

**Hoy no hay una vuelta exacta al OEM demostrada.** Puede reinstalarse una
aplicación propia revisada mientras el rescate siga accesible, pero no restaura
la retroiluminación/funciones OEM ni el contenido original. Una restauración OEM
futura requeriría material correcto y un método auditado/verificado; no se ofrece
como disponible. La copia de referencia no debe presentarse como solución.

Fuentes y decisiones sobre rangos/protección: [primer ensayo](first-flash-trial.md),
[informe de arranque](usb-isp-and-startup.md),
[respaldo histórico](backup-and-recovery.md) y
[evidencia de la unidad](../hardware/first-flash-evidence.json).
