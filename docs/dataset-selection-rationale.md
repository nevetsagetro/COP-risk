# Rationale de selección documental

## Decisión final de búsqueda real

Milestone 4C cierra la tercera y última búsqueda dirigida. Se evaluaron
exactamente tres candidatos:

| Candidato | Resultado |
|---|---|
| PKDD’99 Czech Financial Dataset | **Needs clarification** |
| Kiva public loan/repayment data | **Reject** |
| LendingClub historical loan performance | **Reject** |

Ninguno es `Eligible for quarantine inspection`. La búsqueda real se detiene;
no se descargan datos ni se abre otra ronda.

Resultados anteriores no cambian: SFLLD permanece `Reject`; Home Credit Model
Stability permanece `Needs clarification`; los demás candidatos conservan sus
clasificaciones documentadas.

## Motivos

### PKDD’99 Czech Financial Dataset

Es el mejor encaje estructural de esta ronda: tablas relacionales de clientes,
cuentas, préstamos y transacciones, IDs, fechas, pagos y outcome. Permitiría
separar hechos as-of de transacciones posteriores y plantear un split temporal.

No entra en cuarentena porque el [repositorio histórico VŠE](https://sorry.vse.cz/~berka/challenge/pkdd1999/berka.htm)
no aporta licencia explícita, términos de publicación, snapshot versionado o
hash recuperable. “Problemas de pago” tampoco define default/horizonte con la
precisión contractual. `Needs clarification` es triage, no aprobación parcial.

### Kiva

**Reject.** Kiva ofrece IDs, fechas, repayment schedules y repagos, y sus
[Terms](https://www.kiva.org/legal/terms) describen una regla orientativa de
default. Sin embargo, restringen automatización y contenido y prohíben publicar
borrower delinquency/default individual. El permiso para métricas agregadas y
modelos es unknown bloqueante, no autorización inferida. Además, partners,
extensiones y reporting hacen target/censura no uniformes.

### LendingClub

**Reject.** Los [Terms oficiales](https://www.lendingclub.com/apply/auto/legal-agreement/TermsOfUse)
limitan contenido al uso propio y prohíben republicar, redistribuir o
incorporarlo a otra base. La oferta actual no aporta un snapshot histórico
público, versionado y licenciado que una originación con pagos/outcome. Copias
de Kaggle o terceros no sustituyen esa ausencia.

## Recomendación formal posterior

Se recomienda **datos sintéticos deterministas como bootstrap principal**.
Debe existir un contrato explícito que genere:

- entidades y préstamos repetidos con IDs;
- decisiones y disponibilidad as-of;
- repayment schedules, outcomes, madurez y censura;
- cohortes temporales con cambios controlados;
- atributos de auditoría separados de inputs;
- escenarios reproducibles de drift y retraining.

Este enfoque permite construir y probar el pipeline manual, leakage controls,
split temporal, monitoring y lifecycle sin PII ni restricciones de
redistribución. No sustenta claims de desempeño, calibración, fairness o
utilidad sobre crédito real.

Como variante híbrida futura, un dataset real solo podría usarse para baseline
descriptivo/modelístico después de superar contrato, checklist, cuarentena y
aceptación humana. Los datos sintéticos seguirían reservados para escenarios
controlados de drift/retraining. Hoy ningún candidato real está autorizado
para esa capa; Home Credit Model Stability y PKDD’99 solo pueden reabrirse si
se resuelven documentalmente sus bloqueos.

## Consecuencias

- No se crea ADR ni se selecciona fuente en este milestone.
- No se implementa todavía generador sintético, ingesta, split o modelo.
- El próximo milestone deberá proponer el contrato y alcance del bootstrap
  sintético/híbrido, y cualquier aceptación humana deberá registrarse
  separadamente.
- La evidencia real revisada puede informar limitaciones y diseño, pero no se
  mezcla con datos sintéticos ni se presenta como dataset aprobado.
