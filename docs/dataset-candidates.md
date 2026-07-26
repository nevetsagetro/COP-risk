# Candidatos documentales de dataset

## Estado y método

Investigación exclusivamente documental iniciada el **2026-07-26** y ampliada
el mismo día mediante Milestone 4B. No se
descargaron archivos, no se usaron APIs, no se inspeccionaron filas, no se
aceptaron términos y no se creó ningún dataset o snapshot.

Las etiquetas usadas son:

- **FACT**: afirmación explícita en una fuente enlazada;
- **INFERENCE**: conclusión metodológica derivada de hechos;
- **UNKNOWN**: información no confirmada por las fuentes consultadas;
- **RISK**: condición que podría invalidar o limitar el uso.

La evaluación usa los requisitos de fase A de
`docs/dataset-acceptance-checklist.md` como pre-screening, pero Milestone 4B no
completa ni resuelve esa fase. `Needs clarification` es un estado de triage
documental solicitado, no el resultado normativo `Pending` o `Rejected`, y no
autoriza adquisición.

## Resumen

| Candidato | Propietario/publicador | Resultado | Motivo determinante |
|---|---|---|---|
| Single-Family Loan-Level Dataset, Sample | Freddie Mac | **Reject** | Rechazado tras la inspección de Milestone 4A; no existe aceptación parcial. |
| Default of Credit Card Clients | I-Cheng Yeh / UCI | **Reject** | No demuestra timestamps por observación, madurez ni test temporal defendible. |
| South German Credit | Banco regional no identificado / UCI | **Reject** | Sin IDs o fechas por fila; muestreo estratificado altera la prevalencia. |
| Single-Family Loan Performance Data | Fannie Mae | **Reject** | Los términos publicados son de uso interno y no demuestran compatibilidad con un portfolio público. |

La segunda búsqueda añade tres candidatos. Ninguno está seleccionado o
aceptado para entrenamiento.

## 1. Freddie Mac Single-Family Loan-Level Dataset — Sample

### Fuentes primarias

- [Página oficial del dataset](https://www.freddiemac.com/research/datasets/sf-loanlevel-dataset)
- [General User Guide, enero de 2026](https://www.freddiemac.com/research/pdf/user_guide.pdf)
- [Release Notes, enero de 2026](https://www.freddiemac.com/fmac-resources/research/pdf/release_notes.pdf)
- [FAQ oficial](https://www.freddiemac.com/fmac-resources/research/pdf/faq.pdf)
- [Términos específicos, versión efectiva de noviembre de 2025](https://capitalmarkets.freddiemac.com/crt/docs/pdfs/fre_terms_conditions_sflld.pdf)

Consulta: 2026-07-26.

### Procedencia, población y tamaño

**FACT:** Freddie Mac publica datos de originación, performance mensual y
pérdidas de hipotecas que compró o garantizó. La página vigente describe
aproximadamente 55 millones de hipotecas, originaciones desde 1999 hasta 2025 y
performance hasta septiembre de 2025. La guía distingue un Standard Dataset
actualizado normalmente cada trimestre y un Non-Standard Dataset que ya no se
actualiza. [Página oficial](https://www.freddiemac.com/research/datasets/sf-loanlevel-dataset),
[User Guide, Introduction](https://www.freddiemac.com/research/pdf/user_guide.pdf).

**FACT:** el sample oficial es una muestra aleatoria simple de 50.000 préstamos
por vintage anual completo y una cantidad proporcional para años parciales,
con los mismos campos que el Standard Dataset. El número exacto de registros
mensuales del sample vigente es **UNKNOWN** sin adquirirlo.
[User Guide, Dataset Sample](https://www.freddiemac.com/research/pdf/user_guide.pdf),
[FAQ, Loan Population](https://www.freddiemac.com/fmac-resources/research/pdf/faq.pdf).

**RISK:** la población son préstamos comprados o garantizados por Freddie Mac,
no todas las solicitudes ni todo el mercado hipotecario. El muestreo por
vintage tampoco garantiza pesos temporales representativos para métricas
agregadas.

### Unidad, tiempo, IDs y repetición

**FACT:** el fichero de originación contiene una observación por préstamo y el
fichero de performance múltiples observaciones mensuales enlazadas por un
`Loan Sequence Number` único. Se documentan `Monthly Reporting Period`, primera
fecha de pago, vencimiento, mora, saldo, modificación y eventos de terminación.
[User Guide, File Layout](https://www.freddiemac.com/research/pdf/user_guide.pdf).

**INFERENCE:** son posibles dos contratos futuros distintos: una predicción por
préstamo en originación/adquisición o una predicción comportamental por
préstamo-mes. Ninguno se decide aquí.

**UNKNOWN:** la documentación no confirma un ID estable de prestatario entre
préstamos distintos. El loan ID permite agrupar filas del mismo préstamo, pero
no demuestra ausencia de entity leakage entre préstamos. El instante de
decisión underwriting tampoco queda identificado de forma inequívoca.

### Target, horizonte, madurez y censura

**FACT:** la performance incluye estados mensuales, terminaciones y pérdidas
hasta el cutoff o la disposición; la información de pérdidas puede tener
retraso y puede actualizarse en releases posteriores.
[FAQ, Performance and Loss](https://www.freddiemac.com/fmac-resources/research/pdf/faq.pdf),
[User Guide, Actual Loss](https://www.freddiemac.com/research/pdf/user_guide.pdf).

**INFERENCE:** podría definirse después un evento futuro de mora o crédito con
horizonte fijo. Prepago, venta, modificación y terminación requerirían una
política explícita de eventos competidores o censura.

**UNKNOWN:** target, horizonte, `label_observed_at` y regla de madurez de COP.
No existe un target binario aceptado por el proyecto.

### Leakage, variables sensibles y proxies

**RISK:** para una decisión en originación, mora mensual, modificaciones,
zero-balance, disposición, recuperación y pérdidas son post-decision o
post-outcome. El servicer publicado puede describir el último periodo, no el
instante de decisión. Estos campos serían `prohibited` salvo otro contrato
as-of probado. [User Guide, Origination and Performance Data](https://www.freddiemac.com/research/pdf/user_guide.pdf).

**RISK:** un split aleatorio por fila colocaría el mismo préstamo en varias
particiones. Los enlaces de refinanciación conocidos también deberán agruparse.
State, MSA, ZIP truncado, credit score, DTI y occupancy pueden actuar como
proxies; su presencia no permite hacer claims de fairness.

### Privacidad, licencia y adquisición

**FACT:** la guía documenta masking mediante fechas mensuales, ZIP truncado,
redondeos de ciertos saldos y agrupación de sellers/servicers pequeños.
Masking no demuestra riesgo nulo de reidentificación.
[User Guide, Data Masking](https://www.freddiemac.com/research/pdf/user_guide.pdf).

**FACT:** los términos, efectivos desde noviembre de 2025 y actualizados el
2025-11-03, permiten investigación académica o research y publicar resultados
no comerciales bajo restricciones: no redistribuir el dataset o derivados
reconstructivos y no intentar identificar personas. El acceso requiere
registro. [Términos específicos versionados](https://capitalmarkets.freddiemac.com/crt/docs/pdfs/fre_terms_conditions_sflld.pdf),
[página oficial](https://www.freddiemac.com/research/datasets/sf-loanlevel-dataset).

**UNKNOWN:** si cada artefacto futuro del portfolio encaja en esas condiciones
y qué versión exacta de los términos aceptaría una persona. No se aceptaron
términos en este milestone.

### Split y monitoring

**INFERENCE:** vintages y reporting periods permitirían un split temporal real,
agrupación por loan ID y cohortes reference/current. La performance supervisada
solo sería válida con horizonte maduro y release congelada.

**RISK:** el dataset es “living” y admite correcciones. Un release reciente
puede contener conocimiento retrospectivo; sin release, cutoffs, lista de
ficheros y hashes no existe snapshot reproducible. Cambios de esquema, masking,
población o reporting pueden confundirse con drift.
[User Guide, Introduction](https://www.freddiemac.com/research/pdf/user_guide.pdf),
[Release Notes](https://www.freddiemac.com/fmac-resources/research/pdf/release_notes.pdf).

### Fase A documental

| Requisito | Estado | Evidencia o bloqueo |
|---|---|---|
| Fuente, propietario y procedencia | Pass | Página, guía y release notes oficiales. |
| Licencia/términos de adquisición | Not evidenced | Los términos existen, pero falta confirmación humana sobre portfolio público no comercial. |
| Esquema y diccionario | Pass | User Guide oficial. |
| Acceso seguro | Not evidenced | Registro/login; futuras credenciales deberán ser locales. |
| Anonimización/PII | Not evidenced | Masking documentado, riesgo residual no inspeccionado. |
| Cuarentena y responsable | Not evidenced | No se crea ni designa en este milestone. |

**Resultado vigente: Reject.** Milestone 4A ejecutó la inspección autorizada y
aplicó la checklist completa en
`docs/datasets/sflld-sample-2019-inspection.md`. Este rechazo reemplaza la
recomendación histórica y no constituye aceptación parcial.

## 2. UCI Default of Credit Card Clients

### Fuentes primarias

- [Ficha, DOI y licencia UCI](https://archive.ics.uci.edu/dataset/350/default)
- [Paper original](https://www.sciencedirect.com/science/article/pii/S0957417407006719)

Consulta: 2026-07-26.

### Hechos

**FACT:** UCI publica 30.000 instancias, 23 features, un ID entero, target
binario y licencia CC BY 4.0. Las variables incluyen límite de crédito, sexo,
educación, estado civil, edad y seis meses de repayment, facturas y pagos entre
abril y septiembre de 2005. [Ficha UCI](https://archive.ics.uci.edu/dataset/350/default).

**FACT:** el paper describe titulares de tarjeta de un banco de Taiwán y
default payment, pero su sección de datos declara 25.000 observaciones, frente
a las 30.000 de UCI. La relación exacta entre ambas poblaciones es **UNKNOWN**.
[Paper original](https://www.sciencedirect.com/science/article/pii/S0957417407006719),
[ficha UCI](https://archive.ics.uci.edu/dataset/350/default).

### Evaluación contractual

- **INFERENCE:** cada fila parece representar un titular dentro de una cohorte
  común; los meses son columnas históricas, no observaciones longitudinales.
- **UNKNOWN:** definición operacional exacta de default, cutoff de decisión,
  horizonte, disponibilidad de campos de septiembre, `label_observed_at`,
  censura, estabilidad del ID, duplicados y procedimiento de anonimización.
- **UNKNOWN:** UCI ofrece una ficha con DOI y descarga, pero no documenta un
  release inmutable, hashes oficiales ni un procedimiento para reproducir
  exactamente el artefacto inspeccionado.
- **RISK:** sexo no puede ser input; educación, estado civil y edad requieren
  revisión como atributos sensibles o proxies.
- **RISK:** un split aleatorio solo mediría interpolación en una cohorte de
  2005. No permite test temporal ni reference/current defendibles.

### Fase A documental

| Requisito | Estado | Evidencia o bloqueo |
|---|---|---|
| Fuente, propietario y procedencia | Pass | Ficha UCI, DOI y paper original. |
| Licencia/términos de adquisición | Pass | CC BY 4.0 explícita en UCI. |
| Esquema y diccionario | Pass | Variables publicadas; la temporalidad operacional sigue ausente. |
| Acceso seguro | Pass | La ficha documenta descarga pública; no se accedió a ella. |
| PII/anonimización | Not evidenced | La ficha no aporta evaluación específica. |
| Cuarentena y responsable | Not evidenced | No se crea ni designa en este milestone. |

### Pre-screening documental de fase B — no ejecutada

| Requisito | Estado | Evidencia o bloqueo |
|---|---|---|
| Timestamps, test temporal y madurez | Fail | No se documentan timestamps por observación ni cohortes posteriores. |
| Entity control | Not evidenced | El ID no demuestra estabilidad de entidad ni repetición. |

**Resultado: Reject.** La licencia clara no compensa los rechazos duros
metodológicos.

## 3. UCI South German Credit

### Fuentes primarias

- [Ficha canónica, DOI y licencia UCI](https://archive.ics.uci.edu/dataset/573/south+german+credit+update)
- [Informe de corrección y procedencia](https://www1.bht-berlin.de/FB_II/reports/Report-2019-004.pdf)

Consulta: 2026-07-26.

### Hechos

**FACT:** contiene 1.000 créditos de 1973–1975 de un banco regional del sur de
Alemania: 700 good y 300 bad, 20 predictores y licencia CC BY 4.0. Los bad
credits fueron fuertemente sobremuestreados; el informe sitúa la prevalencia
original alrededor del 5 %. [Ficha UCI](https://archive.ics.uci.edu/dataset/573/south+german+credit+update),
[informe, sección 3](https://www1.bht-berlin.de/FB_II/reports/Report-2019-004.pdf).

**FACT:** el target indica cumplimiento good/bad del contrato. Solo incluye
créditos concedidos. No se publican IDs ni fechas por fila. Varias cantidades
fueron discretizadas o transformadas y el detalle de la transformación del
importe es desconocido. Incluye edad, `personal_status_sex`,
`foreign_worker` y una indicación de teléfono.
[Informe, secciones 3 y Appendix D](https://www1.bht-berlin.de/FB_II/reports/Report-2019-004.pdf).

### Evaluación contractual

- **INFERENCE:** una fila representa un contrato concedido, no la población
  general de solicitudes; existe selection bias por aprobación.
- **UNKNOWN:** entidad, repetición, decisión, outcome, horizonte, madurez,
  censura, availability as-of y anonimización.
- **UNKNOWN:** aunque la ficha canónica identifica DOI `10.24432/C5QG88` y
  ficheros publicados, no aporta hashes ni versionado inmutable del contenido.
- **RISK:** 30 % bad no es prevalencia poblacional; calibración, PR baselines y
  probabilidades quedarían distorsionadas. SMOTE-Tomek sería especialmente
  difícil de justificar sobre una clase ya sobremuestreada.
- **RISK:** atributos sensibles/proxies no pueden ser inputs y la categoría
  combinada tampoco permite una auditoría fiable por sexo.

### Fase A documental

| Requisito | Estado | Evidencia o bloqueo |
|---|---|---|
| Fuente, propietario y procedencia | Pass | UCI, DOI e informe; el banco originador no está identificado. |
| Licencia/términos de adquisición | Pass | CC BY 4.0 explícita en UCI. |
| Esquema y diccionario | Pass | UCI e informe documentan campos y sampling; quedan transformaciones unknown. |
| Acceso seguro | Pass | La ficha documenta descarga pública; no se accedió a ella. |
| PII/anonimización | Not evidenced | Sin evaluación específica vigente. |
| Cuarentena y responsable | Not evidenced | No se crea ni designa en este milestone. |

### Pre-screening documental de fase B — no ejecutada

| Requisito | Estado | Evidencia o bloqueo |
|---|---|---|
| IDs, timestamps y madurez | Fail | Ausentes por observación. |
| Split temporal/grupal | Fail | No puede demostrarse. |

**Resultado: Reject.**

## 4. Fannie Mae Single-Family Loan Performance Data

### Fuentes primarias

- [Página oficial](https://capitalmarkets.fanniemae.com/credit-risk-transfer/single-family-credit-risk-transfer/fannie-mae-single-family-loan-performance-data)
- [Glossary and File Layout](https://www.fanniemae.com/media/24861/display)
- [FAQ oficial](https://capitalmarkets.fanniemae.com/resources/file/credit-risk/pdf/sf-loan-performance-dataset-faqs.pdf)
- [Legal Disclosure](https://www.fanniemae.com/about-us/legal-disclosure)

Consulta: 2026-07-26.

### Hechos

**FACT:** la página describe un subset de hipotecas convencionales
unifamiliares, con información estática de adquisición/originación y
performance mensual hasta liquidación o cutoff. Excluye varios tipos de
producto, requiere registro y puede corregir originación y servicing en
releases posteriores. [Página oficial](https://capitalmarkets.fanniemae.com/credit-risk-transfer/single-family-credit-risk-transfer/fannie-mae-single-family-loan-performance-data).

**FACT:** el diccionario contiene loan identifier, origination/first-payment
dates, reporting mensual, mora, last paid installment, foreclosure,
disposition, recuperaciones y costes. Muchos son campos post-decision para un
modelo en originación. [Glossary](https://www.fanniemae.com/media/24861/display).

**FACT:** el legal disclosure vigente describe Loan Performance Data como
`internal use only` y restringe redistribución y uso comercial externo sin
acuerdo escrito. [Legal Disclosure, sección 7.4.1](https://www.fanniemae.com/about-us/legal-disclosure).

**UNKNOWN:** las fuentes consultadas no fijan en una cifra única el tamaño
aproximado del release vigente ni documentan un artefacto inmutable con hashes.

### Evaluación contractual

- **INFERENCE:** técnicamente permitiría cohortes, repeated loan observations,
  split temporal y performance madura.
- **UNKNOWN:** permiso para publicar modelos, métricas y artefactos derivados
  en un repositorio de portfolio, target/horizonte, borrower identity común y
  riesgo residual de reidentificación.
- **UNKNOWN:** la documentación consultada no ofrece una evaluación específica
  de PII ni un inventario inequívoco de atributos sensibles; geografía,
  crédito, ocupación y características socioeconómicas son proxies
  potenciales que exigirían revisión.
- **UNKNOWN:** el acceso registrado y las correcciones de releases no bastan
  para reproducir una adquisición sin conservar versión, ficheros y hashes.
- **RISK:** “internal use only” no demuestra compatibilidad con el uso público
  previsto. Correcciones históricas y campos de servicing crean además riesgos
  de reproducibilidad y leakage.

### Fase A documental

| Requisito | Estado | Evidencia o bloqueo |
|---|---|---|
| Fuente, propietario y procedencia | Pass | Página y diccionario oficiales. |
| Licencia/términos de adquisición | Fail | Uso público no autorizado explícitamente. |
| Esquema y diccionario | Pass | Originación y performance mensual documentadas. |
| Acceso seguro | Not evidenced | Requiere registro; no se evaluó el mecanismo. |
| PII/anonimización | Not evidenced | Requiere revisión específica. |
| Cuarentena y responsable | Not evidenced | No se crea ni designa en este milestone. |

**Resultado: Reject** para COP mientras no exista permiso escrito compatible.

## Comparación metodológica y de monitoring

| Dimensión | Freddie Sample | UCI Taiwan | South German | Fannie Mae |
|---|---|---|---|---|
| Unidad documentada | Loan + loan-month | Titular/cohorte estática | Crédito concedido | Loan + loan-month |
| ID | Loan ID; borrower ID unknown | ID opaco | Ninguno documentado | Loan ID; borrower ID unknown |
| Tiempo | Originación y performance mensual | Meses como columnas | Solo años agregados | Originación y performance mensual |
| Repetidos | Mensuales por loan | No documentados | Unknown | Mensuales por loan |
| Target COP | UNKNOWN | Default no operacionalizado para COP | Cumplimiento good/bad | UNKNOWN |
| Split temporal | Potencialmente viable | No | No | Potencialmente viable |
| Entity split | Por loan; borrower unknown | No demostrado | No | Por loan; borrower unknown |
| Labels maduras | Derivables tras definir horizonte | No demostradas | No demostradas | Derivables en principio |
| Reference/current | Viable con release congelada | No defendible | No defendible | Técnicamente viable |
| Simulación de drift | Cohortes históricas reales | Artificial | Artificial | Cohortes históricas reales |
| Reproducibilidad | Requiere release + hashes | DOI estable; sin cohortes | DOI estable; sin tiempo | Requiere release + hashes |
| Resultado | Reject | Reject | Reject | Reject |

## Fuentes descartadas como evidencia principal

Mirrors, blogs y copias de Kaggle no se usaron para sostener hechos. Tampoco se
consideró que la política general actual de donación de UCI pruebe
retroactivamente la anonimización de cada dataset histórico.

## Segunda búsqueda limitada — Milestone 4B

Consulta documental: 2026-07-26. Las clasificaciones de esta ronda son
`Reject`, `Needs clarification` y `Eligible for quarantine inspection`. No se
descargaron ficheros, aceptaron reglas o crearon cuentas.

## 5. Home Credit — Credit Risk Model Stability

### Fuentes primarias

- [Página oficial](https://www.kaggle.com/competitions/home-credit-credit-risk-model-stability/overview)
- [Descripción oficial de datos](https://www.kaggle.com/competitions/home-credit-credit-risk-model-stability/data)
- [Reglas oficiales](https://www.kaggle.com/competitions/home-credit-credit-risk-model-stability/rules)
- [Home Credit Group](https://www.homecredit.net/about-us.aspx/)

### Términos y publicación

**FACT:** Home Credit Group figura como host y presenta una tarea de riesgo de
default con estabilidad temporal. La descripción oficial identifica una tabla
base por caso, fecha de decisión, semana y tablas históricas relacionales.

**UNKNOWN bloqueante:** las páginas oficiales existen, pero durante esta
consulta no expusieron sin interacción de Kaggle el texto versionado completo
de las reglas específicas. No se verificó la opción de uso de Competition
Data, permiso para portfolio externo no comercial, publicación de código,
métricas, gráficos, documentación o modelos entrenados. Tampoco se verificó el
tratamiento de parámetros derivados. Sin permiso explícito no hay cuarentena.

**RISK:** la prohibición habitual de redistribuir Competition Data no se
confunde con permiso para publicar otros outputs. Cada output requiere
confirmación en las reglas específicas; no se usa evidencia de participantes.

### Contrato y evaluación

**FACT:** la unidad aparente es una solicitud/caso de crédito. `case_id`
identifica el caso; `date_decision` y `WEEK_NUM` permiten cohortes. Las tablas
históricas contienen relaciones, personas, bureau, contratos y pagos.

**UNKNOWN bloqueante:** la documentación públicamente visible denomina el
target como default, pero no permitió verificar evento, días de atraso,
horizonte, extremos, `label_observed_at`, madurez, censura y eventos
competidores. El nombre `target` no satisface el contrato.

**UNKNOWN:** `case_id` no demuestra una clave estable de cliente. Debe
confirmarse cómo agrupar solicitudes repetidas; de lo contrario existe entity
leakage.

**RISK:** pagos, mora, collections, decisiones o contratos posteriores pueden
ser post-decision/post-outcome. Ventanas y sufijos de features no prueban
`available_at <= date_decision`. Sexo, edad, estado familiar, educación,
geografía y proxies socioeconómicos requieren segregación/revisión.

**INFERENCE:** si entidad, target y reglas as-of se verifican, fecha y semana
permitirían un split temporal y cohortes reference/current. La métrica de
Kaggle no sustituye el protocolo COP ni convierte su leaderboard en test final.

La adquisición/ingesta sería compleja por múltiples tablas CSV/Parquet,
profundidades relacionales, diccionario anonimizado y acceso sujeto a reglas.

**Resultado: Needs clarification.** Antes de cuarentena deben confirmarse por
fuente oficial los usos y outputs permitidos, redistribución, target/horizonte,
madurez, censura, entity ID y disponibilidad as-of.

## 6. Home Credit Default Risk

### Fuentes primarias

- [Página oficial](https://www.kaggle.com/competitions/home-credit-default-risk/overview)
- [Descripción oficial de datos](https://www.kaggle.com/competitions/home-credit-default-risk/data)
- [Reglas oficiales](https://www.kaggle.com/competitions/home-credit-default-risk/rules)
- [Home Credit Group](https://www.homecredit.net/about-us.aspx/)

### Términos y publicación

**FACT:** Home Credit organizó la competición. La tabla principal representa
una solicitud y enlaza bureau, solicitudes previas, POS/cash, tarjetas y pagos.

**UNKNOWN bloqueante:** no se verificó desde el texto oficial accesible la
licencia concreta de Competition Data ni permiso externo para código,
métricas, gráficos, documentación y modelos. No se presume redistribución.

### Contrato y evaluación

**FACT:** el diccionario oficial describe `TARGET=1` como dificultades de pago:
atraso superior a `X` días en al menos una de las primeras `Y` cuotas. `X` e
`Y` están ocultos; evento y horizonte no son reproducibles.

**FACT:** existen offsets relativos de días/meses, pero no fecha calendario de
decisión por solicitud. Los IDs auxiliares enlazan créditos e históricos sin
demostrar una clave de persona estable entre solicitudes.

**RISK:** sin timestamp de decisión por fila no hay test temporal ni
reference/current real. Históricos repetidos causan entity leakage si cruzan
particiones. Pagos, mora y decisiones requieren lineage as-of y pueden incluir
post-outcome.

**RISK:** género, edad, estado familiar, ocupación, vivienda, región y fuentes
externas son atributos protegidos o proxies. No se demuestra vista
`audit_only`, madurez, censura o ausencia de PII/reidentificación.

**INFERENCE:** la estructura relacional ofrece ingesta compleja, pero offsets
internos no ordenan cohortes de decisión para monitoring o drift.

**Resultado: Reject.** Target con constantes ocultas y ausencia de fecha de
decisión por observación son fallos duros; aclarar licencia no los compensa.

## 7. UCI Polish Companies Bankruptcy

### Fuentes primarias

- [Ficha, DOI, diccionario y licencia UCI](https://archive.ics.uci.edu/dataset/365/polish+companies+bankruptcy)
- [Paper original](https://www.sciencedirect.com/science/article/abs/pii/S0957417416301592)

### Términos y publicación

**FACT:** UCI identifica a Sebastian Tomczak como creador, asigna DOI
`10.24432/C5F600` y publica bajo CC BY 4.0. La licencia permite compartir y
adaptar los datos con atribución, por lo que uso no comercial, métricas,
gráficos, documentación que no reconstruya datos y redistribución atribuida
son compatibles. Código independiente no queda restringido por la licencia de
datos. Si un modelo entrenado es una adaptación o un output independiente
requiere revisión específica; no se presume permiso.

**FACT:** UCI declara origen en Emerging Markets Information Service (EMIS).
El paper de Maciej Zięba, Sebastian K. Tomczak y Jakub M. Tomczak, DOI
`10.1016/j.eswa.2016.04.001`, introduce el uso de estos casos para predicción
de bancarrota. La cadena desde EMIS debe confirmarse en una futura inspección
aunque UCI sea la autoridad de licencia del artefacto distribuido.

### Contrato y evaluación

**FACT:** hay cinco casos: ratios del primer al quinto año predicen bancarrota
después de cinco a un año, respectivamente. El target es estado de bancarrota
de la empresa y hay 64 ratios financieros.

**FACT:** UCI informa periodos agregados (quebradas 2000–2012; activas
2007–2013), pero no ID de empresa ni timestamp/año por fila.

**UNKNOWN:** no puede saberse si una empresa aparece en varios casos ni
agruparla. Tampoco se documentan fecha de decisión/bancarrota por fila,
`label_observed_at`, `followup_end`, cutoff, censura o disponibilidad exacta de
los estados financieros.

**RISK:** horizontes distintos no ordenan filas. No hay test temporal ni
control de entity leakage. Ventanas distintas de activas/quebradas pueden
confundir clase y tiempo; estados revisados después del cutoff pueden filtrar
información.

**UNKNOWN:** no hay atributos protegidos adecuados para auditoría; no se
afirma fairness. No aparecen variables nominalmente post-outcome, pero sin
timestamps no puede probarse.

**INFERENCE:** adquisición pública e ingesta tabular serían sencillas y los
horizontes permiten sensibilidad estática, pero no monitoring/drift real.

**Resultado: Reject.** Licencia y target claros no compensan ausencia de
timestamps, entity ID y split temporal defendible.

## Comparación de Milestone 4B

| Dimensión | HC Model Stability | HC Default Risk | Polish Bankruptcy |
|---|---|---|---|
| Propietario/fuente | Home Credit / Kaggle | Home Credit / Kaggle | Tomczak / UCI; origen EMIS |
| Términos | Unknown bloqueante | Unknown bloqueante | CC BY 4.0 |
| Portfolio público | Unknown | Unknown | Permitido con atribución |
| Código/métricas/gráficos/docs | Unknown | Unknown | Datos/adaptaciones permitidos; código independiente |
| Modelos entrenados | Unknown | Unknown | Revisión específica |
| Redistribución | No presumida | No presumida | Permitida con atribución |
| Unidad | Solicitud/caso | Solicitud | Empresa-caso |
| Entidad | Cliente estable unknown | Cliente estable unknown | Empresa ID ausente |
| Decisión/tiempo | Fecha + semana | Offsets relativos | Periodos agregados |
| Target/horizonte | Default completo unknown | X/Y ocultos | Bancarrota 1–5 años |
| Madurez/censura | Unknown | Unknown | No reconstruibles por fila |
| Repetidos/entity leakage | Probables | Históricos relacionales | Solape entre casos unknown |
| Split temporal | Potencial, no demostrado | Imposible actualmente | Imposible |
| Protected/proxies | Requieren segregación | Requieren segregación | Auditoría ausente |
| Post-outcome | Alto riesgo | Alto riesgo | No probado |
| Monitoring/drift | Potencial alto | No defendible | No defendible |
| Adquisición/ingesta | Alta | Alta | Baja/moderada |
| Resultado | **Needs clarification** | **Reject** | **Reject** |

## Resultado de la segunda búsqueda

Ninguno es `Eligible for quarantine inspection`. Credit Risk Model Stability
justifica una aclaración humana limitada, pero no puede descargarse mientras
términos, publicación y target sean ambiguos. Los otros dos se rechazan por
fallos metodológicos. SFLLD conserva **Reject** sin reinterpretación.
