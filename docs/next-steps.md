# Cómo seguir sin abrir el teclado

Actualizado: **2026-10-29**. Esta es la guía de relevo del proyecto.

## 1. Estado actualizado: ya se consultó el ISP de la unidad

Leer primero [USB real, arranque e instalación pendiente](usb-isp-and-startup.md).
La consulta en SSH confirmó familia SN32F26x, CS0 y checksum `0x27d1`; se pidió
retorno y el usuario confirmó que sigue escribiendo. No se escribió flash.

- `custom42` y `default` siguen disponibles; `custom42_fn` agrega F1–F12,
  mantiene cuatro capas y ocupa 17316 B / 1960 B RAM estática con pilas.
- Jumploader propio C/ASM: 436 B, relleno a512, con Escape inferido y magic del
  QMK fijado. Compilado y revisado estáticamente, **no instalado**.
- 50 tests pasan en Linux/macOS. Vial completo, backup propio, matriz real y rescate con app
  fallida siguen pendientes. El checklist sigue devolviendo2.
- Checksum de referencia no coincide bajo los cálculos ensayados; eso no
  demuestra corrupción, pero impide afirmar identidad. No usarlo como backup.

Las secciones de planificación siguientes describen los requisitos generales;
el informe nuevo precisa qué partes de A/B/C/D ya avanzaron y cuáles no.

Vial: consultar [presupuesto real de RAM y alternativa de tres capas](vial-memory-budget.md).
El [nuevo prototipo de lectura Vial](vial-readonly-prototype.md) ya compila:
19460 B flash,1952 B RAM; no es aún configuración editable. Para código,
continuar con diseño/pruebas de persistencia sin duplicar el mapa en RAM.
El usuario aclaró que el HyperX está en Linux local; macOS por SSH es ahora la
fuente principal. No trasladarlo solo para compilar ni asumir USB en el remoto.

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
| **B. Estudiar actualización y recuperación** | Analizar estáticamente protocolo/herramientas e imagen. Determinar entrada/salida del modo de actualización por USB con carcasa cerrada, incluso si QMK no arranca. | Secuencia y alcance respaldados por evidencia. Si solo se puede recuperar con acceso interno, no cumple el límite del usuario. |
| **C. Disponer de acceso USB autorizado** | Trabajar en una sesión que exponga el HyperX al sistema/herramienta de diagnóstico. Este entorno no expone los nodos USB. | Poder seleccionar exclusivamente el HyperX. El cambio de entorno no autoriza flashear ni borra los pasos A/B. No evadir restricciones de esta sesión. |
| **D. Contrastar la unidad** | Verificar información y comportamiento que el protocolo permita sin escribir, desproteger ni restablecer. Separar metadatos, comandos de consulta y cambios de modo. | Relación suficiente con MCU/revisión/imágenes; registrar qué se comprobó y qué sigue inferido. No llamar pasiva a una consulta que reinicia el dispositivo. |
| **E. Resolver restauración** | Buscar paquete auténtico adecuado y verificar qué recupera; evaluar si existe lectura no destructiva. | Ruta realista de retorno, con regiones y límites explícitos. Hoy no hay backup propio ni restauración comprobada. |
| **F. Preparar el primer ensayo** | Solo con lo anterior resuelto, revisar una imagen de prueba mínima y su mapa; explicar incertidumbres residuales antes de escribir. | Selección inequívoca del HyperX, recuperación compatible con carcasa cerrada y plan de verificación. No usar las cinco posiciones averiadas como teclas de rescate. |
| **G. Validar funciones** | Después de un primer arranque comprobado: matriz, USB, teclas simultáneas, rebote, capas, reinicios y uso máximo de pila. | Registro de resultados reales. Después adaptar el mapa al usuario y evaluar Vial/persistencia con el presupuesto restante. |

**Continuar A/B/E según el informe USB/arranque; C ya dispone de acceso por SSH.** Se pueden investigar con archivos
y código públicos; no requieren que el usuario abra ni compre nada.
No hace falta volver a descargar el compilador o repetir builds sin cambios.

Si no se encuentra una recuperación que respete la carcasa cerrada, hay que
decirlo: **no se puede prometer un primer flasheo seguro en esas condiciones**.
La autorización para experimentar no convierte en conocido un método de
recuperación que todavía no está demostrado.

## 4. La ESP32: qué podría aportar y qué no

**No hace falta conectarla ahora.** Falta conocer su modelo exacto; una foto
de la placa o la inscripción del módulo servirían si se decide estudiar esa
alternativa. Esto no implica abrir el HyperX.

- El **ESP32 original**, por ejemplo los módulos ESP32-WROOM-32 habituales, no
  tiene USB nativo; el USB de muchas placas es un conversor USB-serie para
  programar la propia placa. [FAQ oficial de Espressif, sección USB](https://docs.espressif.com/projects/esp-faq/en/latest/esp-faq-en-master.pdf).
- **ESP32-S2/S3** sí admiten USB host y Espressif ofrece un ejemplo HID para
  recibir teclados. El ejemplo consultado usa protocolo Boot, por lo que no
  valida automáticamente todos los reportes del HyperX. [Ejemplo oficial HID](https://github.com/espressif/esp-idf/blob/master/examples/peripherals/usb/host/hid/README.md).
- **Inferencia de diseño:** una placa adecuada podría estudiarse como
  remapeador externo, sin cambiar el firmware del HyperX. No sería este port
  QMK instalado dentro del teclado ni Vial automático. Habría que resolver
  alimentación y cómo enviar las teclas al PC; tener dos conectores USB no
  garantiza dos funciones independientes. El periférico OTG no debe estar
  ocupado a la vez por las pilas host y device. [Documentación USB host de Espressif](https://docs.espressif.com/projects/arduino-esp32/en/latest/api/usb_host.html).

Conectarla únicamente al PC **no la convierte en un programador universal del
HyperX**, no proporciona acceso a su flash y no evita conocer el protocolo de
actualización. No hay instrucciones de cableado, compras o programación de
la ESP32 aprobadas en esta etapa.

## 5. Cómo retomar el trabajo

1. Leer `AGENTS.md` y este documento.
2. Revisar `hardware/validation-status.json`: ARM aprobado significa build y
   ajuste estático, no hardware probado.
3. Ejecutar, si hace falta comprobar el estado local:

```sh
rtk proxy python3 -m unittest discover -s tests -v
rtk proxy python3 scripts/check_port_readiness.py
```

Resultado esperado: **50 pruebas pasan** y el segundo comando sale con **2**,
enumerando revisión, matriz, bootloader, recuperación y jumploader pendientes.
Ninguno de los dos comandos accede al teclado.

Registrar toda nueva evidencia en [la bitácora](project-log.md). Mantener el
Silakka54 completamente fuera del trabajo y no presentar la imagen del espejo
ni el archivo `*.analysis-only.bin` como un respaldo de la unidad.
