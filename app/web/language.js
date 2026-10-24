(() => {
  const translations = {
    en: {
      htmlLang: "en",
      toggleLabel: "Cambiar a español",
      toggleText: "ES",
      heroCopy: "A visual walkthrough of how a model is selected, evaluated and used to prioritize a bounded review policy on the Home Credit benchmark.",
      warning: "Not approved for real credit decisions.",
      stories: [
        ["Inspect", "We verify the Home Credit snapshot, entity split and feature contract."],
        ["Compare", "We search candidates with train cross-validation and validate the selected models."],
        ["Prioritize", "We compare how many observed defaults each model finds under a review capacity."],
      ],
      targetEyebrow: "WHAT THE HOME CREDIT MODEL PREDICTS",
      targetTitle: "Can the supplied application be associated with the source target?",
      targetText: "The static benchmark uses the source-provided TARGET exactly as documented. It is an academic classification outcome, not a new prediction horizon and not a credit approval or rejection decision.",
      targetExample: ["Input", "Application data and prior-history aggregates", "Output", "Academic probability for the source TARGET"],
      quickEyebrow: "QUICK TOUR",
      quickTitle: "If you only have two minutes",
      quickItems: ["Inspect the Home Credit snapshot and split contract.", "Compare selected models and their validation metrics.", "Move from model scores to a bounded review policy."],
      jumpLinks: ["1 · Home Credit results", "2 · Decide under capacity", "3 · UCI reference", "4 · Explore the reference demo"],
      metricsEyebrow: "UCI REFERENCE BASELINE",
      metricsTitle: "What question does each reference metric answer?",
      metricsLead: "These are not approval scores. They are different ways to describe model errors.",
      chart1Eyebrow: "UCI REFERENCE · CHART 01",
      chart1Title: "Can the reference baseline separate defaults?",
      chart1Lead: "Each point is a different alert threshold. The curve closest to the top-left finds more defaults with fewer false alarms.",
      chart2Eyebrow: "UCI REFERENCE · CHART 02",
      chart2Title: "How are reference probabilities distributed?",
      chart2Lead: "Each bar groups cases with a similar estimated probability. The tallest bar only shows where there are more cases.",
      thresholdEyebrow: "UCI REFERENCE · INTERACTIVE LAB",
      thresholdTitle: "What did the reference threshold trade off?",
      predictionEyebrow: "UCI REFERENCE DEMO",
      predictionTitle: "Explore the original UCI case flow",
      predictionLead: "Choose a scenario to see the full flow, and open the details only if you want to experiment with each variable.",
      journeyEyebrow: "THE FULL STORY",
      journeyTitle: "From dataset to final model decision",
      journeyLead: "COP keeps the reasoning visible: first we define what the data can support, then we train and compare models, and only then do we choose an academic operating point. Each step has a different role.",
      homeStoryNav: ["01 · Context", "02 · Data", "03 · Features", "04 · Iterations", "05 · Validation", "06 · Policy", "07 · Conclusion"],
      homeChapters: [["What is the model estimating?", "The Home Credit baseline estimates the probability of the source-provided TARGET for an application enriched with static historical aggregates. It is a classification experiment, not a new lending decision or a temporal forecast.", "Interpretation", "A probability ranks academic cases by estimated association with the target; it is not a certainty."], ["Which evidence is open to the model?", "We fit on train, select with train cross-validation, evaluate the selected candidates on validation, and keep the final test unopened. The split is entity-disjoint and static because the source archive has no defensible application timestamp.", "What this protects", "Selection decisions do not use the final test."], ["How does raw data become model input?", "The pipeline keeps the application table as the anchor and adds grouped aggregates from public historical tables. The groups describe the engineering path; they do not establish causality.", "Feature contract", "Audit-only columns remain outside model inputs."], ["How did the candidate improve?", "Each point is a controlled trial. The mean shows train cross-validation Average Precision; the whisker shows fold variation. The selected point is the best candidate under the declared primary metric.", "Selection rule", "Choose by train-CV Average Precision, then inspect validation once."], ["Did the selected candidates hold outside cross-validation?", "Train-CV supports selection; validation is the separate check. Ranking metrics and probability-error metrics answer different questions, so they are shown with their own scales.", "Read it carefully", "A validation result is evidence for this static split, not a production guarantee."], ["What changes when review capacity changes?", "Instead of pretending one threshold is universal, we rank validation cases and vary the fraction available for review. More capacity usually finds more target-positive cases while reducing precision.", "Policy reading", "Capacity is an operating assumption, not a model metric."], ["What can we conclude?", "", "Boundary", "Static benchmark only. No temporal stability, production validity, or real-credit claim."]],
      journeySteps: [["01 · DATASET", "Start with a public source", "Home Credit Default Risk, 307,511 applications and four source tables used for static aggregates.", "Target: TARGET as supplied"], ["02 · CONTRACT", "Define what is allowed", "Audit-only fields stay outside model inputs and historical aggregates use relative pre-application records.", "Use: static academic benchmark only"], ["03 · SPLITS", "Protect the evidence", "Entity-disjoint train and validation splits support static comparison; test remains unopened.", "215,024 train · 46,281 validation · 46,206 test"], ["04 · EXPERIMENT", "Try controlled candidates", "Logistic Regression and LightGBM are evaluated with reproducible train cross-validation and recorded parameters.", "Selection metric: Average Precision"], ["05 · OPERATING POLICY", "Prioritize under capacity", "Cases are ranked by estimated probability and review budgets are tested at 1%, 5%, 10% and 20%.", "Primary policy view: precision@capacity"], ["06 · DECISION", "Make a bounded academic conclusion", "LightGBM is currently strongest under the declared static validation protocol. This does not authorize production use.", "Final test: closed by default"]],
    },
    es: {
      htmlLang: "es",
      toggleLabel: "Cambiar a inglés",
      toggleText: "EN",
      heroCopy: "Un recorrido visual para entender cómo se selecciona y evalúa un modelo y cómo prioriza una política de revisión acotada en Home Credit.",
      warning: "No autorizado para decisiones crediticias reales.",
      stories: [["Inspeccionar", "Verificamos el snapshot, el split por entidad y el contrato de variables de Home Credit."], ["Comparar", "Buscamos candidatos con cross-validation en train y validamos los modelos seleccionados."], ["Priorizar", "Comparamos cuántos impagos observados encuentra cada modelo con una capacidad de revisión limitada."]],
      targetEyebrow: "QUÉ PREDICE EL MODELO HOME CREDIT",
      targetTitle: "¿Puede asociarse la solicitud al target de origen?",
      targetText: "El benchmark estático usa exactamente el TARGET proporcionado por la fuente. Es un resultado académico de clasificación, no un nuevo horizonte ni una decisión de aprobación o rechazo.",
      targetExample: ["Entrada", "Datos de solicitud y agregados del historial previo", "Salida", "Probabilidad académica del TARGET de origen"],
      quickEyebrow: "RECORRIDO RÁPIDO",
      quickTitle: "Si solo tienes dos minutos",
      quickItems: ["Inspecciona el snapshot y el contrato de splits de Home Credit.", "Compara los modelos seleccionados y sus métricas de validation.", "Pasa de los scores a una política de revisión acotada."],
      jumpLinks: ["1 · Resultados Home Credit", "2 · Decidir con capacidad", "3 · Referencia UCI", "4 · Explorar referencia"],
      metricsEyebrow: "BASELINE UCI DE REFERENCIA",
      metricsTitle: "¿Qué pregunta responde cada métrica de referencia?",
      metricsLead: "No son notas de aprobación. Son distintas formas de describir los errores del modelo.",
      chart1Eyebrow: "REFERENCIA UCI · GRÁFICO 01",
      chart1Title: "¿Puede el baseline de referencia separar impagos?",
      chart1Lead: "Cada punto es una línea de alerta diferente. La curva más cercana a la esquina superior izquierda encuentra más impagos con menos falsas alarmas.",
      chart2Eyebrow: "REFERENCIA UCI · GRÁFICO 02",
      chart2Title: "¿Cómo se distribuyen las probabilidades de referencia?",
      chart2Lead: "Cada barra agrupa casos con una probabilidad parecida. La barra más alta solo dice dónde hay más casos.",
      thresholdEyebrow: "REFERENCIA UCI · LABORATORIO INTERACTIVO",
      thresholdTitle: "¿Qué intercambiaba el threshold de referencia?",
      predictionEyebrow: "DEMO UCI DE REFERENCIA",
      predictionTitle: "Explora el flujo de casos UCI original",
      predictionLead: "No necesitas inventar 19 valores. Elige un escenario para ver el flujo completo y abre los detalles solo si quieres experimentar.",
      journeyEyebrow: "LA HISTORIA COMPLETA",
      journeyTitle: "Del dataset a la decisión final del modelo",
      journeyLead: "COP mantiene visible el razonamiento: primero definimos qué puede soportar el dato, después entrenamos y comparamos modelos y sólo entonces elegimos un punto de operación académico. Cada paso tiene una función distinta.",
      homeStoryNav: ["01 · Contexto", "02 · Datos", "03 · Variables", "04 · Iteraciones", "05 · Validación", "06 · Política", "07 · Conclusión"],
      homeChapters: [["¿Qué estima el modelo?", "El baseline de Home Credit estima la probabilidad del TARGET proporcionado por la fuente para una solicitud enriquecida con agregados históricos estáticos. Es un experimento de clasificación, no una nueva decisión crediticia ni una predicción temporal.", "Interpretación", "Una probabilidad ordena casos académicos según su asociación estimada con el target; no es una certeza."], ["¿Qué evidencia está abierta al modelo?", "Ajustamos en train, seleccionamos con cross-validation en train, evaluamos los candidatos seleccionados en validation y mantenemos cerrado el test final. El split no comparte entidades y es estático porque el archivo no tiene un timestamp defendible.", "Qué protege", "Las decisiones de selección no usan el test final."], ["¿Cómo se convierte el dato bruto en entrada?", "El pipeline usa la tabla de solicitudes como ancla y añade agregados agrupados de tablas históricas públicas. Los grupos describen el proceso de ingeniería; no demuestran causalidad.", "Contrato de variables", "Los campos audit-only quedan fuera de las entradas del modelo."], ["¿Cómo mejoró el candidato?", "Cada punto es un trial controlado. La media muestra Average Precision en cross-validation de train y la barra muestra la variación entre folds. El punto seleccionado es el mejor bajo la métrica primaria declarada.", "Regla de selección", "Elegir por Average Precision en train-CV y revisar después validation."], ["¿Se mantuvo fuera de cross-validation?", "Train-CV sirve para seleccionar; validation es la comprobación separada. Las métricas de ranking y de error probabilístico responden preguntas distintas y usan escalas propias.", "Cómo leerlo", "Validation es evidencia para este split estático, no una garantía productiva."], ["¿Qué cambia con la capacidad de revisión?", "En lugar de asumir un threshold universal, ordenamos los casos de validation y variamos la fracción disponible para revisión. Más capacidad suele encontrar más positivos, pero reduce la precisión.", "Lectura de política", "La capacidad es un supuesto operativo, no una métrica del modelo."], ["¿Qué podemos concluir?", "", "Límite", "Benchmark estático únicamente. Sin claims de estabilidad temporal, validez productiva ni crédito real."]],
      journeySteps: [["01 · DATASET", "Partir de una fuente pública", "Home Credit Default Risk, 307.511 solicitudes y cuatro tablas de origen usadas para agregados estáticos.", "Target: TARGET de origen"], ["02 · CONTRATO", "Definir qué está permitido", "Los campos audit-only quedan fuera y los agregados históricos usan registros relativos previos a la solicitud.", "Uso: benchmark estático académico"], ["03 · SPLITS", "Proteger la evidencia", "Los splits de train y validation no comparten entidades; test permanece cerrado.", "215.024 train · 46.281 validation · 46.206 test"], ["04 · EXPERIMENTO", "Probar candidatos controlados", "Logistic Regression y LightGBM se evalúan con cross-validation reproducible en train y parámetros registrados.", "Métrica de selección: Average Precision"], ["05 · POLÍTICA DE OPERACIÓN", "Priorizar con capacidad limitada", "Ordenamos por probabilidad y probamos capacidades de revisión del 1%, 5%, 10% y 20%.", "Vista principal: precision@capacity"], ["06 · DECISIÓN", "Llegar a una conclusión académica acotada", "LightGBM es actualmente el candidato más fuerte bajo el protocolo estático declarado. No autoriza uso productivo.", "Test final: cerrado por defecto"]],
    },
  };

  const text = (selector, value) => {
    const element = document.querySelector(selector);
    if (element) element.textContent = value;
  };

  const html = (selector, value) => {
    const element = document.querySelector(selector);
    if (element) element.innerHTML = value;
  };

  const applyLanguage = (language) => {
    const copy = translations[language];
    document.documentElement.lang = copy.htmlLang;
    const toggle = document.querySelector("#language-toggle");
    if (toggle) {
      toggle.textContent = copy.toggleText;
      toggle.setAttribute("aria-label", copy.toggleLabel);
    }
    text(".hero-copy", copy.heroCopy);
    text(".warning", copy.warning);
    document.querySelectorAll(".story-card").forEach((card, index) => {
      const title = card.querySelector("h2");
      if (title) title.textContent = copy.stories[index][0];
      const paragraph = card.querySelector("p");
      if (paragraph) paragraph.textContent = copy.stories[index][1];
    });
    text(".target-card .eyebrow", copy.targetEyebrow);
    text(".target-card h2", copy.targetTitle);
    text(".target-card p", copy.targetText);
    const example = document.querySelector(".target-example");
    if (example) {
      example.querySelectorAll("span")[0].textContent = copy.targetExample[0];
      example.querySelectorAll("b")[0].textContent = copy.targetExample[1];
      example.querySelectorAll("span")[1].textContent = "→";
      example.querySelectorAll("span")[2].textContent = copy.targetExample[2];
      example.querySelectorAll("b")[1].textContent = copy.targetExample[3];
    }
    text(".quick-start .eyebrow", copy.quickEyebrow);
    text(".quick-start h2", copy.quickTitle);
    document.querySelectorAll(".quick-start li").forEach((item, index) => { item.textContent = copy.quickItems[index]; });
    document.querySelectorAll(".jump-links a").forEach((item, index) => { item.textContent = copy.jumpLinks[index]; });
    document.querySelectorAll(".home-story-nav a").forEach((item, index) => { item.textContent = copy.homeStoryNav[index]; });
    document.querySelectorAll("[data-story-chapter]").forEach((chapter, index) => {
      const values = copy.homeChapters[index];
      if (!values) return;
      chapter.querySelector(".home-chapter-copy h2").textContent = values[0];
      const paragraph = chapter.querySelector(".home-chapter-copy > p");
      if (paragraph && values[1]) paragraph.textContent = values[1];
      chapter.querySelector(".story-checkpoint b").textContent = values[2];
      chapter.querySelector(".story-checkpoint span").textContent = values[3];
    });
    text("#metrics-panel .eyebrow", copy.metricsEyebrow);
    text("#metrics-panel h2", copy.metricsTitle);
    text("#metrics-panel > .lead", copy.metricsLead);
    text("#roc-panel .eyebrow", copy.chart1Eyebrow);
    text("#roc-panel h2", copy.chart1Title);
    text("#roc-panel > .lead", copy.chart1Lead);
    text("#probability-panel .eyebrow", copy.chart2Eyebrow);
    text("#probability-panel h2", copy.chart2Title);
    text("#probability-panel > .lead", copy.chart2Lead);
    text("#threshold-panel .eyebrow", copy.thresholdEyebrow);
    text("#threshold-panel h2", copy.thresholdTitle);
    text(".prediction-panel .eyebrow", copy.predictionEyebrow);
    text(".prediction-panel h2", copy.predictionTitle);
    text(".prediction-panel > .lead", copy.predictionLead);
    text("#journey-panel .eyebrow", copy.journeyEyebrow);
    text("#journey-panel h2", copy.journeyTitle);
    text("#journey-panel > .lead", copy.journeyLead);
    document.querySelectorAll(".journey-step").forEach((step, index) => {
      const values = copy.journeySteps[index];
      if (!values) return;
      step.querySelector("span").textContent = values[0];
      step.querySelector("h3").textContent = values[1];
      step.querySelector("p").textContent = values[2];
      step.querySelector("small").innerHTML = values[3].replace(/([^:]+):/, "<b>$1:</b>");
    });
    localStorage.setItem("cop-language-v2", language);
    document.dispatchEvent(new CustomEvent("cop-language-change", { detail: language }));
  };

  const stored = localStorage.getItem("cop-language-v2");
  let language = stored === "es" ? "es" : "en";
  document.querySelector("#language-toggle")?.addEventListener("click", () => {
    language = language === "es" ? "en" : "es";
    applyLanguage(language);
  });
  applyLanguage(language);
})();
