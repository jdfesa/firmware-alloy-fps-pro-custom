# Usar y configurar el teclado

Esta guía corresponde al candidato `vial_editable` instalado y probado. Para
riesgos de instalación o actualización, leer [seguridad](safety-and-recovery.md).

## Desbloquear antes de editar

> [!IMPORTANT]
> **Después de cada reconexión el teclado vuelve bloqueado.** Los mapas se
> conservan y funcionan, pero no se aceptan escrituras hasta iniciar Unlock.

En Vial de escritorio, seleccionar HyperX y abrir **Security → Unlock desde la
barra superior de macOS**. Mantener Tab+Caps hasta completar la barra y soltar.
El GUI consulta cada 200 ms; el protocolo requiere 20 pasos, aproximadamente 4 s.
No basta pulsar la combinación sin abrir primero esa ventana.

Desbloquear una vez permite editar varias teclas/capas durante esa conexión.
Reconectar, reiniciar o elegir Security → Lock vuelve a bloquear. Para escribir
normalmente no se necesita desbloquear ni tener Vial abierto.

## Asignar una tecla

1. Elegir capa 0, 1, 2 o 3.
2. Hacer clic en la posición destino del teclado superior.
3. Elegir el código en la paleta inferior, por ejemplo Basic → E.
4. Cada asignación admitida se guarda automáticamente en flash.

No se escribe con la tecla física para asignarla. La selección puede avanzar
a la siguiente posición tras un cambio: comprobar la capa y el destino antes
del siguiente clic. `▽`/`KC_TRNS` hereda el comportamiento inferior; `KC_NO`
deshabilita. Fn usa MO(1) inicialmente. El tiempo de tapping se compila en
200 ms, no se ajusta desde QMK Settings en esta variante.

## Si no cambia o no persiste

| Síntoma | Comprobación |
| --- | --- |
| Mantener Tab+Caps no hace nada | Iniciar primero Security → Unlock y mantener hasta completar la barra. |
| No se guarda después de reconectar | Volver a desbloquear antes de editar; no hace falta reflashear. |
| El dibujo cambió, pero al releer no | Puede ser SET rechazado por bloqueo o código no admitido; no confiar solo en el dibujo. |
| Edité otra tecla o capa | Verificar capa, posición y avance automático de selección. |
| Desktop no lo detecta pero web sí | La variante actual incluye la marca USB pública de Vial; un candidato antiguo podía carecer de ella. No confundir una definición cargada manualmente con el firmware correcto. |
| Timeout o conflicto de conexión | Cerrar por completo app (⌘Q), pestañas web y herramientas RAW; reconectar solo HyperX sin Escape. No declarar resuelta la causa general por un ciclo exitoso. |

No todos los códigos visibles en Vial están implementados. Leer la tabla de
[funciones admitidas](status-and-limits.md#qué-admite-la-variante-actual).
Las escrituras fallidas de una herramienta no se reintentan a ciegas.

## Cómo se verificó la persistencia

La prueba GUI efectiva cambió A/S/D de capa 1 a E. Se leyeron los 896 bytes antes
y después de desconectar/reconectar; fueron idénticos y Fn+A escribió E en un
editor de macOS. Después el usuario desbloqueó, restauró las tres posiciones a
transparentes y volvió a reconectar. La relectura completa coincidió con el mapa
inicial: cero diferencias, teclado bloqueado. No quedaron cambios de prueba.

Esta prueba valida esos casos, no todos los códigos de Vial ni una importación
masiva. El ensayo Q→Z previo fue por una herramienta acotada, no esta prueba GUI.

## Uso responsable del almacenamiento

Los cambios admitidos no requieren C ni compilación. Ampliar funciones o capas
sí requiere desarrollo y actualización de firmware. No usar cambios de mapa
continuos como animación: cada edición distinta reemplaza 17 páginas; hay límites
de desgaste. Cerrar Vial no pierde las asignaciones.

## Las 87 posiciones del gráfico y las cinco averiadas

El gráfico actual dibuja todas las teclas por estética. Solo 82 se consideran
utilizables. Las cinco averiadas siguen con `KC_NO` y no aceptan asignaciones
no nulas; pueden verse vacías o como deshabilitadas en la GUI. Su presencia no
prueba reparación. Intentar un código rechazado puede volver a bloquear las
escrituras: repetir Unlock antes de editar una posición admitida.

Una reparación física futura no fue realizada ni autorizada en este proyecto;
verificarla y rehabilitar esas posiciones sería una etapa aparte. No se promete
que el defecto sean pistas ni que todas las averías sean reparables.

## Escape no es el desbloqueo de edición

- Conectar sin Escape: arranque normal y uso de Vial.
- Menú Security→Unlock seguido de Tab+Caps: editar mapas, sin cambiar la app.
- Conectar manteniendo Escape: modo ISP para actualización/rescate revisados,
  antes de la app; no es necesario para cambiar una asignación en Vial.

En ISP no esperar escritura normal ni el configurador. No desconectar mientras
se programa. Ante una entrada accidental sin ninguna escritura en curso, se
puede reconectar sin Escape para intentar volver a la app. Una entrada ISP no
es autorización para flashear: leer [seguridad](safety-and-recovery.md).

## Error de comunicación al iniciar Vial desktop

Se observó en Vial0.7.5/macOS15.5 `RuntimeError: failed to communicate with the
device`, con la traza en `reload_via_protocol`/`hid_send`. Esa consulta precede a
la descarga de la definición: no es una excepción del parser del dibujo ni
prueba por sí misma que el gráfico de87posiciones sea inválido. La causa general
no se aisló. No ejecutar herramientas RAW en paralelo para intentar arreglarlo.

Cerrar Vial por completo, cerrar la web y reconectar HyperX sinEscape antes de
reabrir puede permitir continuar; no se presenta como garantía ni reparación
probada de la causa. Si reaparece, conservar el error y comprobar versiones,
clientes y comunicación de forma aislada, sin borrar mapas ni reflashear a ciegas.
Después de una recarga fallida no confiar en un dibujo anterior: confirmar una
carga exitosa y distinguir cinco casillas `KC_NO` vacías de posiciones ausentes.
