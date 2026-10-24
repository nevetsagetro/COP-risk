(() => {
  const translations = {
    en: {
      htmlLang: "en",
      toggleLabel: "Cambiar a español",
      toggleText: "ES",
      heroCopy: "A visual walkthrough of how a model estimates the probability of a default next month and how the result changes when the alert threshold moves.",
      warning: "Not approved for real credit decisions.",
      stories: [
        ["Predict", "The model estimates the probability of a default next month."],
        ["Compare", "We check how many risk cases it finds and how many alerts are correct."],
        ["Explore", "We move the threshold to see what we gain and what we give up."],
      ],
      targetEyebrow: "WHAT THE MODEL PREDICTS",
      targetTitle: "Will a default be recorded next month?",
      targetText: "The academic dataset contains credit histories. For each case, the model returns an estimated probability of a default next month. It does not predict income, approval, or credit rejection.",
      targetExample: ["Input", "Payment history, balances and payments made", "Output", "Academic probability of a next-month default"],
      quickEyebrow: "QUICK TOUR",
      quickTitle: "If you only have two minutes",
      quickItems: ["Read the three metrics: coverage, alert accuracy and balance.", "Compare both models in their cards without mixing their curves.", "Move the threshold and watch what each model gains and loses."],
      jumpLinks: ["1 · Understand", "2 · Rank", "3 · Experiment"],
      metricsEyebrow: "EVIDENCE",
      metricsTitle: "What question does each metric answer?",
      metricsLead: "These are not approval scores. They are different ways to describe model errors.",
      chart1Eyebrow: "CHART 01 · COMPARISON",
      chart1Title: "Can it separate defaults from on-time payments?",
      chart1Lead: "Each point is a different alert threshold. The curve closest to the top-left finds more defaults with fewer false alarms.",
      chart2Eyebrow: "CHART 02 · DISTRIBUTION",
      chart2Title: "How likely does it estimate that default to be?",
      chart2Lead: "Each bar groups cases with a similar estimated probability. The tallest bar only shows where there are more cases.",
      thresholdEyebrow: "INTERACTIVE LAB",
      thresholdTitle: "What do we gain by moving the alert?",
      predictionEyebrow: "MODEL DEMO",
      predictionTitle: "Enter an academic case",
      predictionLead: "Choose a scenario to see the full flow, and open the details only if you want to experiment with each variable.",
      journeyEyebrow: "THE FULL STORY",
      journeyTitle: "From dataset to final model decision",
      journeyLead: "COP keeps the reasoning visible: first we define what the data can support, then we train and compare models, and only then do we choose an academic operating point. Each step has a different role.",
      journeySteps: [["01 · DATASET", "Start with a public source", "UCI Default of Credit Card Clients, 30,000 rows and 19 approved input variables.", "Target: default_payment_next_month"], ["02 · CONTRACT", "Define what is allowed", "Missing values fail validation. Protected/audit-only attributes stay physically outside the model inputs.", "Use: academic baseline only"], ["03 · SPLITS", "Protect the evidence", "Train is used to fit and tune, validation compares decisions, and test remains unopened until explicit finalization.", "21,000 train · 4,500 validation · 4,500 test"], ["04 · EXPERIMENT", "Try controlled candidates", "Logistic Regression, LightGBM and KNN are evaluated with reproducible cross-validation and recorded parameters.", "Selection metric: Average Precision"], ["05 · OPERATING POINT", "Translate scores into alerts", "The threshold is learned from train out-of-fold predictions; F1 explains the balance between coverage and alert accuracy.", "Default reference: 0.50 · tuned threshold shown in Model Development"], ["06 · DECISION", "Make a bounded academic conclusion", "Run Model Development to identify the strongest candidate under the selected metric. This does not authorize production use.", "Final test: closed by default"]],
    },
    es: {
      htmlLang: "es",
      toggleLabel: "Cambiar a inglés",
      toggleText: "EN",
      heroCopy: "Un recorrido visual para entender cómo un modelo estima la probabilidad de que se registre un impago el próximo mes y cómo cambia el resultado al mover la línea de alerta.",
      warning: "No autorizado para decisiones crediticias reales.",
      stories: [["Predecir", "El modelo estima la probabilidad de impago registrado el próximo mes."], ["Comparar", "Comprobamos cuántos casos encuentra y cuántas alertas son correctas."], ["Explorar", "Movemos el threshold para ver qué ganamos y qué cedemos."]],
      targetEyebrow: "QUÉ PREDICE EL MODELO",
      targetTitle: "¿Se registrará un impago el próximo mes?",
      targetText: "El dataset académico contiene casos de personas con historial de crédito. Para cada caso, el modelo devuelve una probabilidad estimada de que aparezca un impago el mes siguiente. No predice ingresos, aprobación ni rechazo de crédito.",
      targetExample: ["Entrada", "Historial de pagos, saldos y pagos realizados", "Salida", "Probabilidad académica de impago próximo"],
      quickEyebrow: "RECORRIDO RÁPIDO",
      quickTitle: "Si solo tienes dos minutos",
      quickItems: ["Lee las tres métricas: cobertura, acierto y equilibrio.", "Compara los dos modelos en sus tarjetas, sin mezclar sus curvas.", "Mueve el threshold y observa qué gana y qué pierde cada uno."],
      jumpLinks: ["1 · Entender", "2 · Ordenar", "3 · Experimentar"],
      metricsEyebrow: "EVIDENCIA",
      metricsTitle: "¿Qué preguntas responde cada métrica?",
      metricsLead: "No son notas de aprobación. Son distintas formas de describir los errores del modelo.",
      chart1Eyebrow: "GRÁFICO 01 · COMPARACIÓN",
      chart1Title: "¿Puede separar impagos de pagos puntuales?",
      chart1Lead: "Cada punto es una línea de alerta diferente. La curva más cercana a la esquina superior izquierda encuentra más impagos con menos falsas alarmas.",
      chart2Eyebrow: "GRÁFICO 02 · DISTRIBUCIÓN",
      chart2Title: "¿Cómo de probable estima ese impago?",
      chart2Lead: "Cada barra agrupa casos con una probabilidad parecida. La barra más alta solo dice dónde hay más casos.",
      thresholdEyebrow: "LABORATORIO INTERACTIVO",
      thresholdTitle: "¿Qué ganamos al mover la alerta?",
      predictionEyebrow: "DEMO DE MODELO",
      predictionTitle: "Introduce un caso académico",
      predictionLead: "No necesitas inventar 19 valores. Elige un escenario para ver el flujo completo y abre los detalles solo si quieres experimentar.",
      journeyEyebrow: "LA HISTORIA COMPLETA",
      journeyTitle: "Del dataset a la decisión final del modelo",
      journeyLead: "COP mantiene visible el razonamiento: primero definimos qué puede soportar el dato, después entrenamos y comparamos modelos y sólo entonces elegimos un punto de operación académico. Cada paso tiene una función distinta.",
      journeySteps: [["01 · DATASET", "Partir de una fuente pública", "UCI Default of Credit Card Clients, 30.000 filas y 19 variables de entrada aprobadas.", "Target: default_payment_next_month"], ["02 · CONTRATO", "Definir qué está permitido", "Los valores ausentes hacen fallar la validación. Los atributos protegidos/audit-only quedan fuera físicamente de las entradas.", "Uso: baseline académico"], ["03 · SPLITS", "Proteger la evidencia", "Train ajusta y afina, validation compara decisiones y test permanece cerrado hasta una finalización explícita.", "21.000 train · 4.500 validation · 4.500 test"], ["04 · EXPERIMENTO", "Probar candidatos controlados", "Logistic Regression, LightGBM y KNN se evalúan con cross-validation reproducible y parámetros registrados.", "Métrica de selección: Average Precision"], ["05 · PUNTO DE OPERACIÓN", "Convertir scores en alertas", "El threshold se aprende con predicciones out-of-fold de train; F1 explica el equilibrio entre cobertura y acierto.", "Referencia: 0.50 · threshold ajustado en Model Development"], ["06 · DECISIÓN", "Llegar a una conclusión académica acotada", "Ejecuta Model Development para identificar el candidato más fuerte según la métrica elegida. No autoriza uso productivo.", "Test final: cerrado por defecto"]],
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
  };

  const stored = localStorage.getItem("cop-language-v2");
  let language = stored === "es" ? "es" : "en";
  document.querySelector("#language-toggle")?.addEventListener("click", () => {
    language = language === "es" ? "en" : "es";
    applyLanguage(language);
  });
  applyLanguage(language);
})();
