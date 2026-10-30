# Preparación para un repositorio público

Revisión local: **2026-10-29**. El usuario desea publicar el proyecto en GitHub.
**Git local inicializado en `main`, sin commits ni remoto configurado. No se creó
ni publicó un repositorio remoto.**

## Resultado y alcance

En los archivos candidatos a publicación no se detectaron credenciales con
los patrones revisados, correos electrónicos, rutas de usuario locales,
direcciones IP privadas ni identificadores de etiqueta con el formato revisado.
Esto es una revisión acotada, **no una garantía de ausencia de todo secreto**.
No se examinó información ajena a esta carpeta ni se enviaron archivos a un
servicio de análisis externo.

Se encontraron rutas personales en `AGENTS.md`, informes locales y archivos de
bloqueo del editor. Se retiró la referencia personal de `AGENTS.md` y se
excluyeron los informes y temporales afectados, sin borrarlos ni cerrar el
editor del usuario. Las reglas RTK siguen documentadas en el propio archivo.

La foto original de la etiqueta no se copió al proyecto. No se publican
números de serie, SP ni códigos de esa foto. El SKU, VID/PID, nombre del modelo,
familia MCU y hashes de artefactos son información técnica, no identificadores
secretos de la unidad. La documentación menciona las preferencias del usuario,
el Silakka54 y la ESP32; ese contexto quedaría visible al publicar.

## Qué se permite y qué se excluye

**Candidatos públicos:** fuentes propias del port y scripts, pruebas,
documentación, matriz inferida, estado de validación y lock de herramientas.
En `artifacts/analysis` solo están permitidos estos metadatos revisados:

- `arm-build-custom42.json`
- `arm-build-default.json`
- `extraction.json`
- `vendor-provenance.json`

**Excluidos por defecto:** herramientas y dependencias descargadas, firmware
propietario y actualizador, DLL, builds experimentales, desensamblado del
proveedor, exportaciones REA sin sanear, logs, informes de tamaños/símbolos,
fotos, temporales del editor y configuraciones locales de agentes/cloud.
Las reglas también previenen adiciones accidentales de varios formatos comunes
de credenciales. No representan un detector exhaustivo de secretos.

La selección se verificó con Git en un repositorio temporal dentro de `/tmp`,
usando esta carpeta únicamente como árbol de trabajo y sin modificar su `.git`.
Se comprobaron 11 casos de exclusión, incluidos locks de editor, fotos,
actualizador, configuración local y reportes crudos. No se usó `git add -f`.

## Comprobaciones antes del primer push

1. Revisar la lista **real** de archivos staged y su diff; no subir la carpeta
   completa como ZIP ni forzar archivos ignorados.
2. Si existe historial previo fuera de lo accesible en esta sesión, revisarlo
   también. La revisión inicial se hizo antes de inicializar Git. Ahora existe
   el repositorio local en `main`, todavía sin commits; revisar su índice real
   antes del primer commit. La simulación anterior no lo reemplaza.
3. `.gitignore` no retira archivos ya versionados ni borra sus versiones del
   historial. [Explicación oficial de GitHub](https://docs.github.com/en/get-started/git-basics/ignoring-files).
4. Revisar el nombre/correo usados en los futuros commits si no se desea
   publicar el correo personal. No se cambió la configuración Git del usuario.
5. **Elegir una licencia antes de invitar a reutilizar el código.** Aún no hay
   archivo `LICENSE`. Revisar las licencias de cualquier código de terceros que
   se incorpore; no se ha certificado autorización para redistribuir el updater
   o la imagen propietaria, que se mantienen excluidos.
6. Mantener visible que se trata de un **port experimental independiente**:
   QMK compilado, no instalado ni validado en hardware; Vial pendiente y sin
   relación oficial con HyperX. No publicar una release como «estable».

Comandos orientativos para una sesión con repositorio Git real, sin publicar:

```sh
rtk git status --short
rtk git diff --cached --stat
rtk git diff --cached
rtk git ls-files
```

La revisión debe repetirse si se agregan capturas, logs, paquetes, configuraciones
o nuevos metadatos. Ninguna regla impide que un `git add -f` los fuerce.

## Nombre recomendado

**`hyperx-alloy-fps-pro-qmk`**: identifica marca, modelo y tecnología objetivo.
Es más específico que `firmware-alloy-fps-pro-custom`. La descripción sugerida:

> Port QMK experimental para HyperX Alloy FPS Pro: matriz inferida, mapa de
> 42 teclas y cuatro capas. Sin validación en hardware; Vial pendiente.

No incluiría `vial` ni `stable` en el nombre actual porque no están demostrados.
No se renombró la carpeta local ni se eligió un nombre remoto por el usuario.
El nombre del repositorio en GitHub puede diferir del de la carpeta local.

## Ampliación de revisión: prototipo de lectura Vial

Se añaden fuentes C/headers, JSON de distribución eléctrica generado desde la
matriz existente, generador Python, tests y referencias de protocolo con
hashes/URLs públicos. El UID del prototipo es de diseño, no un serial de unidad.
No se incorporan credenciales SSH ni ubicaciones de red al repositorio. La
whitelist de cuatro JSON en `artifacts/analysis` **no se amplió**: los nuevos
manifiestos, logs y binarios siguen ignorados. No se publicó ni creó remoto.
Mantener la advertencia READ-ONLY y la revisión de licencia antes del primer push.
