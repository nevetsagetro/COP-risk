# Registro de adquisición de SFLLD Sample 2019

## Estado y límites

Este registro describe un artefacto local ya proporcionado para inspección
controlada. No demuestra que Freddie Mac SFLLD Sample 2019 esté aprobado para
entrenamiento, no acepta términos en nombre de ninguna persona y no autoriza
publicar o redistribuir los datos.

- Fecha de inspección: 2026-07-26.
- Estado del candidato: **Reject**.
- Ruta local recibida: `data/raw/sample_2019.zip`.
- Cuarentena: `data/raw/sflld/2019/quarantine/`.
- Responsable de la inspección técnica: agente `coordinator`.
- Aprobador humano, versión de términos aceptada y política de retención:
  pendientes; estos rechazos duros no evidenciados producen `Reject` con la
  evidencia actual.

La autorización de esta tarea permitió registrar e inspeccionar el fichero,
pero no resuelve la compatibilidad jurídica del uso futuro ni la aceptación
del snapshot para entrenamiento.

## Base del repositorio

La inspección comenzó sobre `HEAD`
`ac3eb78c713829cfbe62799a8a1bb22ec2c68212`, con `git status --short` sin
salida. El contrato, protocolo y checklist vigentes son
`docs/data-contract.md`, `docs/evaluation-protocol.md` y
`docs/dataset-acceptance-checklist.md`.

## Identidad material

| Artefacto | Tamaño (bytes) | SHA-256 |
|---|---:|---|
| ZIP recibido | 29,035,641 | `66bd8abbf119b773b717957a5dcfd1279fc035c2912abe144bb4c54442fdcfc1` |
| Originación extraída | 7,758,569 | `62a0f8d66a238d7422859ed2d5fd852061a9b2c44b539173c89236c898a8b894` |
| Servicing extraído | 159,607,046 | `e5f7bc10014ee12e121433aacbb03c0f888e3815247fc30fe791a0c38f7a9023` |

`file` identificó el origen como ZIP deflate y los dos ficheros extraídos como
texto ASCII. Los permisos observados en los tres artefactos fueron `0644`.
El mtime local del ZIP fue `2026-07-26 10:36:34 +0200`; no se interpreta como
fecha oficial del release.

## Controles previos y extracción

Se ejecutaron primero, en el orden solicitado:

```text
git check-ignore -v data/raw/sample_2019.zip
sha256sum data/raw/sample_2019.zip
stat data/raw/sample_2019.zip
file data/raw/sample_2019.zip
unzip -t data/raw/sample_2019.zip
unzip -l data/raw/sample_2019.zip
```

El entorno no incluía inicialmente `unzip`: el primer intento devolvió
`command not found` y una instalación global falló por falta de permisos. Se
descargó el paquete Ubuntu `unzip 6.0-28ubuntu4.1` en `/tmp`, sin modificar
dependencias del proyecto, y se ejecutó su binario real mediante un `PATH`
temporal. `unzip -t` confirmó ambos miembros como `OK` y ausencia de errores;
`unzip -l` confirmó exactamente:

- `sample_orig_2019.txt`, 7,758,569 bytes;
- `sample_svcg_2019.txt`, 159,607,046 bytes.

Antes de extraer, una comprobación adicional de la central directory confirmó
dos miembros, extensiones `.txt`, ausencia de cifrado, symlinks, rutas
absolutas, `..` y separadores invertidos. No había ejecutables ni miembros
adicionales. La extracción se limitó a la nueva ruta de cuarentena indicada.

## Control de Git y publicación

`git check-ignore -v` atribuye el ZIP y ambos TXT a la regla `data/**` de
`.gitignore`. Las carpetas pueden aparecer por las excepciones que permiten
placeholders, pero el contenido material permanece ignorado. Ninguna fila,
identificador ni valor fuente se copió a documentación o configuración.

## Procedencia pendiente

Los nombres y el layout son consistentes con la guía oficial de enero de 2026,
pero el fichero local no incluye una firma o manifest oficial que demuestre por
sí mismo el endpoint, momento de descarga, cutoff exacto o cadena de custodia.
También siguen pendientes la aceptación humana de los términos aplicables y la
compatibilidad de todos los outputs públicos previstos. Por ello, el hash
registra este artefacto local; no constituye aceptación de procedencia,
licencia, selección ni entrenamiento.
