# Rationale de selección documental

## Decisión actual

No se selecciona ni acepta un dataset. La decisión humana continúa pendiente.
La investigación del 2026-07-26 recomienda avanzar únicamente con la revisión
humana previa a una posible inspección en cuarentena del **Freddie Mac
Single-Family Loan-Level Dataset Sample**.

Su estado es **Needs controlled inspection**, no `Eligible` ni `Accepted`.
No se autoriza descarga, registro, aceptación de términos o creación de
cuarentena mediante este documento.

## Criterios aplicados

Se aplicaron el contrato, protocolo y fase A de la checklist vigentes:

- procedencia y términos verificables;
- unidad, IDs y temporalidad documentados;
- posibilidad de preservar un test temporal;
- reconstrucción de labels maduras y censura;
- segregación de información post-decision;
- protección de PII y atributos sensibles;
- snapshots y monitoring futuro;
- compatibilidad del uso con un portfolio público no comercial.

Un dataset manejable o con licencia permisiva no compensa la ausencia de
timestamps, entity control o madurez.

## Candidato recomendado para futura inspección en cuarentena

### Freddie Mac SFLLD Sample

Se recomienda como siguiente candidato porque su
[página oficial](https://www.freddiemac.com/research/datasets/sf-loanlevel-dataset)
y [User Guide](https://www.freddiemac.com/research/pdf/user_guide.pdf)
documentan originación, loan ID, performance mensual, cutoffs, masking y un
sample oficial. Sus
[términos versionados, efectivos desde noviembre de 2025](https://capitalmarkets.freddiemac.com/crt/docs/pdfs/fre_terms_conditions_sflld.pdf)
contemplan investigación y resultados públicos no comerciales con límites de
redistribución, reconstrucción y reidentificación.

La recomendación es condicional porque aún debe decidirse humanamente:

1. si COP y todos sus outputs públicos encajan en el uso no comercial
   permitido;
2. quién aceptaría y conservaría la versión exacta de los términos;
3. qué resultados y artefactos podrían publicarse sin reconstruir los datos;
4. quién sería responsable de la cuarentena, acceso, retención y eliminación;
5. qué release/sample acotado se solicitaría;
6. si el proyecto estudiará originación o préstamo-mes;
7. qué target, horizonte y eventos competidores propondrá después.

Hasta resolver los puntos 1–4 no se supera la fase A y no debe adquirirse.

## Candidatos rechazados

### UCI Default of Credit Card Clients

**Reject.** Aunque UCI publica CC BY 4.0, 30.000 instancias y un diccionario,
no documenta timestamps por observación, availability del cutoff, madurez,
censura ni cohortes temporales para reservar un test futuro.
[Fuente UCI](https://archive.ics.uci.edu/dataset/350/default).

La discrepancia entre las 30.000 instancias de UCI y las 25.000 declaradas en
la sección de datos del [paper original](https://www.sciencedirect.com/science/article/pii/S0957417407006719)
añade una cuestión de versionado. Sexo sería `audit_only/prohibited` y otros
demográficos son proxies potenciales.

### UCI South German Credit

**Reject.** La
[fuente UCI canónica](https://archive.ics.uci.edu/dataset/573/south+german+credit+update)
y el [informe de corrección](https://www1.bht-berlin.de/FB_II/reports/Report-2019-004.pdf)
documentan 1.000 créditos de 1973–1975 y sobremuestreo de bad credits. No hay
IDs o fechas por fila, horizonte operacional ni madurez verificable. La
prevalencia enriquecida y el sesgo por aprobación invalidan una demostración
simple de calibración o generalización.

### Fannie Mae Single-Family Loan Performance Data

**Reject** bajo los términos publicados. La estructura longitudinal sería útil,
pero el [Legal Disclosure](https://www.fanniemae.com/about-us/legal-disclosure)
describe los datos como `internal use only`. No se infiere permiso para
publicar modelos, métricas o artefactos de portfolio. Solo podría reabrirse la
evaluación con autorización escrita compatible.

## Información que debe verificarse después de una adquisición autorizada

Para Freddie Mac Sample, una futura fase B deberá verificar:

- versión de términos, release, cutoffs, ficheros y hashes;
- esquema real frente al User Guide;
- cardinalidad y unicidad de `Loan Sequence Number`;
- enlaces de refinanciación, duplicados, gaps y secuencias mensuales;
- missing, códigos especiales y correcciones retrospectivas;
- ausencia de nombres, direcciones, texto libre u otra PII residual;
- riesgo de reidentificación y proxies geográficos/crediticios;
- instante de decisión as-of y disponibilidad de cada feature;
- separación de originación, servicing y outcome;
- target, horizonte, prepago, censura, modificaciones y reporting lags;
- viabilidad de train/validation/calibration/test temporal y agrupado;
- reproducibilidad sin redistribuir el artefacto.

## Rechazo inmediato durante la inspección

El candidato se rechazará si:

- los términos no cubren el uso real o los outputs públicos previstos;
- aparece PII o la procedencia deja de ser verificable;
- no puede congelarse y reproducirse el release;
- no existe un instante de decisión reconstruible;
- el loan ID y enlaces conocidos no permiten controlar entity leakage;
- el target/horizonte o la madurez no pueden reconstruirse;
- campos post-decision/post-outcome son inseparables;
- atributos sensibles no pueden excluirse de inputs;
- no puede reservarse un test temporal intacto.

## Recomendación humana pendiente

Se solicita una decisión humana sobre si autorizar **solo el gate documental
previo** para Freddie Mac SFLLD Sample:

- confirmar uso público no comercial y límites de publicación;
- aceptar o rechazar los términos específicos vigentes;
- designar responsable y política de cuarentena;
- autorizar, en una tarea posterior separada, una release/sample exactos.

Sin esa aprobación, el estado permanece `Needs controlled inspection`. Este
documento no constituye asesoramiento jurídico ni un ADR de selección.
