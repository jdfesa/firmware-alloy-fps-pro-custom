# Continuación del proyecto

Revisión documental: 2026-10-31. Resultados de hardware al 2026-10-30.
Entrada principal: [README](../README.md).

## Punto de partida confirmado

- TKL editable instalado; 87 posiciones dibujadas, 82 útiles y cuatro capas.
- Vial desktop detecta y permite asignaciones admitidas después de Unlock.
- GUI → flash → desconexión/reconexión → salida humana verificado en capa 1.
- Las tres posiciones de prueba se restauraron desde GUI: relectura completa
  de 896 B idéntica al mapa inicial, cero diferencias y relock comprobado.
- Instalador macOS app-only y Escape→ISP probados con alcance documentado.
- 107 tests pasan en Mac; no estabilidad general ni backup/restauración OEM.

## Retomar sin repetir errores

1. Leer [uso](usage.md), [estado/límites](status-and-limits.md) y
   [seguridad](safety-and-recovery.md). No hace falta reflashear para configurar.
2. Para editar tras reconectar: **Security → Unlock**, luego mantener Tab+Caps
   hasta completar la barra. Solo pulsar las teclas no inicia nada.
3. Comparar cambios antes de sincronizar copias del repositorio. No sobrescribir
   trabajo diferente sin revisión. Compilar no requiere mover el teclado ni
   disponer de dos equipos; ver [requisitos por tarea](reproduction.md).
4. Mantener evidencia pública saneada y bitácora al avanzar. Commits en inglés,
   push explícito al remoto existente; no publicar artefactos ignorados.

## Trabajo útil siguiente, no una autorización de nuevas escrituras

1. Configurar el mapa ergonómico deseado con los códigos admitidos; elegir
   sustitutos para one-shot/multimedia u otros todavía no implementados.
2. Medir high-water de pilas, reconexiones/USB, matriz completa, simultáneas y
   rebote. No confundir 80 B de heap con margen de pila.
3. Evaluar una función adicional por vez, empezando por las necesarias para
   ese flujo de trabajo; medir antes de prometer que caben.
4. Investigar más capas solo con formato/reserva/migración y recuperación de
   mapas revisados. No es un botón de GUI ni un límite universal de Vial.
5. Iluminación requiere controlador/identificación validada; no activar pines
   inferidos sin sustento ni pedir abrir la carcasa.
6. Mantener como pendientes revisión electrónica exacta, restauración OEM,
   ensayo de app deliberadamente corrupta y estabilidad prolongada.
7. Mejorar preparación reproducible de un clon limpio y completar la revisión
   de atribuciones de terceros. La licencia del repositorio está en [LICENSE](../LICENSE).

## Lo que no cambia

Carcasa cerrada y operaciones limitadas al HyperX. Sin updater/DLL propietario,
unprotect, mass erase ni rangos adivinados. Escape es una entrada de rescate
observada, no un backup OEM ni garantía de recuperación universal.

El checklist general sigue devolviendo2 por evidencias pendientes, no porque
haya fallado el remapeo demostrado. No alterar validaciones para forzar READY.

## Historia para entender decisiones anteriores

[Plan anterior completo](first-trial-planning-history.md),
[proceso y decisiones](process-and-decisions.md) y [bitácora](project-log.md).
Los informes fechados pueden decir «no instalado» o «solo compilado» respecto de
su fase; no usarlos como estado actual.
