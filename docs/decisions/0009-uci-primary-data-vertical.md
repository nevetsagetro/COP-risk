# ADR 0009: UCI como vertical principal de datos

- Status: Accepted
- Date: 2026-08-02

## Contexto

La generación sintética permitió cerrar decisiones metodológicas tempranas,
pero creó una dependencia accidental: módulos UCI reutilizaban hashing y carga
YAML desde `cop.data.synthetic`. Eso impedía ejecutar el pipeline UCI desde un
checkout que no incluyera la vertical sintética.

## Decisión

UCI Default of Credit Card Clients es el dataset principal del proyecto. Su
uso continúa limitado al baseline académico aceptado por ADR 0008. La vertical
UCI solo puede depender de módulos neutrales bajo `cop.data` y nunca de
`cop.data.synthetic`.

Las utilidades reutilizables de hashing viven en `cop.data.hashing` y la carga
YAML estricta en `cop.data.yaml`. El paquete sintético queda aislado; puede
consumir utilidades neutrales, pero no forma parte de la vertical UCI.

## Consecuencias

- adquisición, evaluación, snapshot y splits UCI son importables sin synthetic;
- no se borra el trabajo sintético existente;
- esta decisión no autoriza modelos, entrenamiento ni nuevos claims;
- UCI sigue sin autorizar temporalidad, monitoring longitudinal, fairness,
  producción o decisiones crediticias reales.
