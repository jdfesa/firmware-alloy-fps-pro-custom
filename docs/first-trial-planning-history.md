# Historia de la planificación del primer ensayo

> [!NOTE]
> Plan de las fases 2026-10-29/30, anterior a la primera escritura. Conserva
> propuestas, criterios y pendientes de entonces; el ensayo ya ocurrió.
> Para el estado vigente usar [estado y límites](status-and-limits.md) y
> [continuación](next-steps.md). Resultados en [primer ensayo](first-flash-trial.md).

## 0. Prioridad entonces acordada: rescate mínimo y primera prueba, no perfección previa

Se priorizó un primer ensayo con una vía mínima para volver a programar otro
candidato si el primero fallaba. **No se exigió restauración OEM exacta como
condición previa absoluta.** Esto no prueba que el
rescate exista ni autoriza comandos/offsets desconocidos.

**Ruta a evaluar primero, reutilizando lo existente:** el pequeño jumploader
entra al ISP antes de ejecutar QMK; la tecla de rescate propuesta es Escape.
Ya hay código para ello, no hace falta crear otro sistema de configuración.
Su lectura C0/A0 está inferida y no probada eléctricamente. El rechazo de
vectores inválidos ayuda, pero no detecta una aplicación que tiene vectores
correctos y luego se cuelga. El rescate manual debe cubrir ese caso.

### Trabajo mínimo que sí afecta a la primera prueba

1. Revisar el protocolo de programación y las unidades/rangos de borrado para
   preservar el ISP y, en iteraciones posteriores, el jumploader. No confundir
   una dirección de salto al ISP con garantía de ROM inmutable.
2. Sustentar el arranque y la entrada de rescate independiente de la aplicación,
   con su incertidumbre residual explícita. No instalar el jumploader solo
   encima del OEM enlazado en cero. Revisar el conjunto de arranque+aplicación.
3. Elegir el candidato mínimo ya disponible, sin exigir edición Vial en el
   primer arranque. Revisar imagen, regiones y condiciones concretas del ensayo.
4. Al probar, priorizar reenumeración y entrada al rescate; después teclas. Si
   falla QMK pero el ISP sigue accesible, cambiar solo la aplicación. No repetir
   escrituras a ciegas ni seguir si desaparece la única ruta de rescate.

**Qué no debe retrasar por sí solo ese ensayo:** recuperar exactamente cada
byte OEM, iluminación, mapa final de42 teclas, todas las funciones Vial o una
GUI perfecta. La geometría de persistencia editable puede esperar si el primer
candidato no escribe mapas en flash; la geometría necesaria para instalarlo no.

No se puede probar el jumploader en la unidad antes de instalarlo por primera
vez. La distinción es: revisión técnica suficiente
antes del ensayo, validación real durante él. **La primera instalación sigue
teniendo riesgo residual**, especialmente si falla el propio arranque o la
tecla inferida; no se promete una unidad imposible de bloquear.

Como alternativa mínima a Vial se contempló una distribución equivalente a la
de fábrica mediante un firmware funcional. Si no arranca ninguna aplicación,
no basta con «dejar el mapa de fábrica»: primero debe funcionar el rescate y
después alguna aplicación. Esto tampoco repara las cinco posiciones averiadas.

Los apartados siguientes conservan el plan completo. La restauración OEM sigue
siendo deseable, pero no debe confundirse con este nuevo objetivo mínimo. El
comprobador actual es el checklist general, no un permiso ni un selector de
primer ensayo; sigue marcando evidencias pendientes y no se cambiaron a `true`.

## 1. Estado previo a la primera escritura: consulta ISP completada

Leer primero [USB real, arranque e instalación pendiente](usb-isp-and-startup.md).
La consulta en SSH confirmó familia SN32F26x, CS0 y checksum `0x27d1`; se pidió
retorno y se confirmó escritura humana posterior. No se escribió flash.

- `custom42` y `default` siguen disponibles; `custom42_fn` agrega F1–F12,
  mantiene cuatro capas y ocupa 17316 B / 1960 B RAM estática con pilas.
- Jumploader propio C/ASM: 436 B, relleno a512, con Escape inferido y magic del
  QMK fijado. Compilado y revisado estáticamente, **no instalado**.
- 62 tests pasan en Linux/macOS. Vial completo, backup propio, matriz real y rescate con app
  fallida siguen pendientes. El checklist sigue devolviendo2.
- Checksum de referencia no coincide bajo los cálculos ensayados; eso no
  demuestra corrupción, pero impide afirmar identidad. No usarlo como backup.

Las secciones de planificación siguientes describen los requisitos generales;
el informe nuevo precisa qué partes de A/B/C/D ya avanzaron y cuáles no.

Vial: consultar [presupuesto real de RAM y alternativa de tres capas](vial-memory-budget.md).
El [nuevo prototipo de lectura Vial](vial-readonly-prototype.md) ya compila:
19460 B flash,1952 B RAM; no es aún configuración editable. Para código,
el [almacén C simulado](vial-map-store.md) ya evita duplicar el mapa en RAM y
pasa29.266 escenarios de fallos. Falta backend físico, desgaste/latencia y
adaptación al escaneo/protocolo; no habilitar escrituras antes de verificar
geometría y recuperación. La compilación de esa fase se realizó en Linux con
fuentes sincronizadas por SSH; compilar no requería mover el teclado.

## 2. Qué significa «arranque auxiliar», explicado sin electrónica

**No es una placa adicional, ni un cable, ni hay que abrir el teclado para
añadir una pieza.** Aquí se habla de un programa muy pequeño que vive en la
memoria del mismo controlador.

Al encender, el controlador necesita saber dónde comenzar a ejecutar. La base
SonixQMK elegida espera que un pequeño programa inicial lo dirija hacia QMK.
Ese programa se llama **jumploader**: aproximadamente, «el que salta al programa».

Una analogía: QMK es una habitación preparada, pero la entrada de la casa debe
llevar hasta ella. Tener la habitación construida no garantiza que la puerta
de entrada apunte al sitio correcto.

Lo observado en este proyecto:

```text
Imagen de fábrica extraída:  comienza en la dirección 0.
Candidato QMK compilado:     comienza en la dirección 512 (hexadecimal 0x200).
Plataforma elegida:          espera un programa inicial que lo dirija allí.
```

No se puede escribir el `.bin` en cero esperando que se corrija solo. Tampoco
está demostrado que conservar los primeros 512 bytes del programa de fábrica
sirva de puente. Eso puede dejar el teclado sin arrancar.

El requisito se ve en el [linker de la revisión fijada de ChibiOS-Contrib](https://github.com/SonixQMK/ChibiOS-Contrib/blob/4b5588b511c0e98b4ae8c3b81357e4468ec9d1cb/os/common/startup/ARMCMx/compilers/GCC/ld/SN32F260.ld).
**No significa que todo firmware de teclado necesite este auxiliar**: es una
condición de la base SonixQMK usada aquí. Cambiar a un arranque directo exigiría
revisar la plataforma, los vectores y las interrupciones; no basta con cambiar
un número del linker.

### No confundir tres funciones

- **Firmware QMK:** escanea teclas y aplica capas durante el uso.
- **Jumploader:** inicia esa aplicación según lo que espera esta plataforma.
- **Modo de actualización/bootloader:** permite recibir firmware desde el PC.
  Hay que comprobar cómo entrar y volver a él en esta unidad, especialmente
  si la aplicación falla.

Bootmagic con Escape ya está incluido en el candidato, pero depende de que
QMK arranque y escanee bien. **No es un salvavidas independiente**.

## 3. Qué falta y cómo avanzar, en orden

| Paso | Trabajo necesario | Evidencia de salida / límite |
| --- | --- | --- |
| **A. Estudiar el arranque** | Revisar el jumploader SonixQMK aplicable a SN32F268F y el inicio del OEM. Identificar direcciones, interrupciones y qué región reemplazaría. | Diseño documentado con fuentes/revisiones y mapa de escritura; no concatenar binarios a ciegas. Puede hacerse sin tocar el teclado. |
| **B. Estudiar actualización y recuperación** | Analizar estáticamente protocolo/herramientas e imagen. Determinar entrada/salida del modo de actualización por USB con carcasa cerrada, incluso si QMK no arranca. | Secuencia y alcance respaldados por evidencia. Si solo se puede recuperar con acceso interno, no cumple el alcance de carcasa cerrada. |
| **C. Disponer de acceso USB autorizado** | Disponer de acceso al HyperX desde el sistema/herramienta de diagnóstico. En el entorno inicial no estaban expuestos los nodos USB. | Poder seleccionar exclusivamente el HyperX. El cambio de entorno no autoriza flashear ni borra los pasos A/B. No evadir restricciones de acceso. |
| **D. Contrastar la unidad** | Verificar información y comportamiento que el protocolo permita sin escribir, desproteger ni restablecer. Separar metadatos, comandos de consulta y cambios de modo. | Relación suficiente con MCU/revisión/imágenes; registrar qué se comprobó y qué sigue inferido. No llamar pasiva a una consulta que reinicia el dispositivo. |
| **E. Resolver restauración** | Buscar paquete auténtico adecuado y verificar qué recupera; evaluar si existe lectura no destructiva. | Ruta realista de retorno, con regiones y límites explícitos. Hoy no hay backup propio ni restauración comprobada. |
| **F. Preparar el primer ensayo** | Solo con lo anterior resuelto, revisar una imagen de prueba mínima y su mapa; explicar incertidumbres residuales antes de escribir. | Selección inequívoca del HyperX, recuperación compatible con carcasa cerrada y plan de verificación. No usar las cinco posiciones averiadas como teclas de rescate. |
| **G. Validar funciones** | Después de un primer arranque comprobado: matriz, USB, teclas simultáneas, rebote, capas, reinicios y uso máximo de pila. | Registro de resultados reales. Después adaptar la distribución deseada y evaluar Vial/persistencia con el presupuesto restante. |

**Continuar A/B/E según el informe USB/arranque; C ya dispone de acceso por SSH.** Se pueden investigar con archivos
y código públicos, sin desmontaje ni compra de hardware.
No hace falta volver a descargar el compilador o repetir builds sin cambios.

Si no se encuentra una recuperación que respete la carcasa cerrada, hay que
decirlo: **no se puede prometer un primer flasheo seguro en esas condiciones**.
La autorización para experimentar no convierte en conocido un método de
recuperación que todavía no está demostrado.

## 4. Comprobaciones previstas en esa fase

1. Leer los criterios del ensayo y sus fuentes.
2. Revisar `hardware/validation-status.json`: ARM aprobado significa build y
   ajuste estático, no hardware probado.
3. Ejecutar, si hace falta comprobar el estado local:

```sh
rtk proxy python3 -m unittest discover -s tests -v
rtk proxy python3 scripts/check_port_readiness.py
```

Resultado registrado entonces: **62 pruebas pasan** y el segundo comando sale con **2**,
enumerando revisión, matriz, bootloader, recuperación y jumploader pendientes.
Ninguno de los dos comandos accede al teclado.

Registrar toda nueva evidencia en [la bitácora](project-log.md). No presentar
la imagen del espejo ni el archivo `*.analysis-only.bin` como respaldo de la unidad.
