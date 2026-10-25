const labels = {
  LIMIT_BAL: "Credit limit", PAY_0: "Payment status · September", PAY_2: "Payment status · August", PAY_3: "Payment status · July", PAY_4: "Payment status · June", PAY_5: "Payment status · May", PAY_6: "Payment status · April",
  BILL_AMT1: "Balance · September", BILL_AMT2: "Balance · August", BILL_AMT3: "Balance · July", BILL_AMT4: "Balance · June", BILL_AMT5: "Balance · May", BILL_AMT6: "Balance · April",
  PAY_AMT1: "Payment made · September", PAY_AMT2: "Payment made · August", PAY_AMT3: "Payment made · July", PAY_AMT4: "Payment made · June", PAY_AMT5: "Payment made · May", PAY_AMT6: "Payment made · April"
};
const paymentStatuses = [[-2,"No consumption"],[-1,"On-time payment"],[0,"No delay"],[1,"1 month late"],[2,"2 months late"],[3,"3 months late"],[4,"4 months late"],[5,"5 months late"],[6,"6 months late"],[7,"7 months late"],[8,"8 months late"],[9,"9+ months late"]];
const defaults = {LIMIT_BAL:50000, BILL_AMT1:20000, BILL_AMT2:20000, BILL_AMT3:20000, BILL_AMT4:20000, BILL_AMT5:20000, BILL_AMT6:20000};
const categorical = new Set(["PAY_0","PAY_2","PAY_3","PAY_4","PAY_5","PAY_6"]);
const state = { sweeps:{}, timer:null, features:{}, baseFeatures:{}, overrides:{}, examples:[], activeExample:null, homeAcademic:null, activeDataset:"home" };
const fmt = (value) => `${(Number(value) * 100).toFixed(1)}%`;
const readableTestStatus = (status) => status === "unopened" ? "final test held out for final evaluation" : status;
const chartColors = {
  logistic_regression: "#2563eb",
  lightgbm: "#0f766e",
  catboost: "#64748b",
  xgboost: "#111827",
  mlp: "#7c3aed",
  knn: "#94a3b8",
  reference: "#94a3b8",
  precision: "#2563eb",
  recall: "#0f766e",
  f1: "#7c3aed",
  warning: "#b45309"
};
const chartTheme = {
  paper_bgcolor: "transparent",
  plot_bgcolor: "transparent",
  font: {family: "Inter, ui-sans-serif, system-ui, sans-serif", color: "#172033", size: 12},
  hoverlabel: {bgcolor: "#ffffff", bordercolor: "#cbd5e1", font: {color: "#172033", size: 12}},
  colorway: [chartColors.logistic_regression, chartColors.lightgbm, chartColors.mlp, chartColors.reference]
};
const plotConfig = {displayModeBar:false, scrollZoom:false, responsive:true};
const originalNewPlot = Plotly.newPlot.bind(Plotly);
const originalReact = Plotly.react.bind(Plotly);
const themedLayout = (layout={}) => ({...chartTheme, ...layout, font:{...chartTheme.font, ...(layout.font||{})}, hoverlabel:{...chartTheme.hoverlabel, ...(layout.hoverlabel||{})}});
Plotly.newPlot = (target, data, layout, config) => originalNewPlot(target, data, themedLayout(layout), config);
Plotly.react = (target, data, layout, config) => originalReact(target, data, themedLayout(layout), config);
const MODEL_LAB_SESSION_KEY = "cop-model-lab-session-v1";
const api = async (path, options={}) => { const response = await fetch(path, options); if (!response.ok) throw new Error(await response.text()); return response.json(); };
function resizeCharts(scope) {
  const resize = () => document.querySelectorAll(`${scope} .js-plotly-plot`).forEach(chart => {
    if (chart.isConnected && chart.offsetWidth > 0 && chart.offsetHeight > 0) {
      Plotly.Plots.resize(chart);
    }
  });
  requestAnimationFrame(resize);
  requestAnimationFrame(() => requestAnimationFrame(resize));
  window.setTimeout(resize, 120);
  window.setTimeout(resize, 400);
}

function resizeUciCharts() { resizeCharts("#tab-uci"); }

function renderMetrics(data) {
  const body = document.querySelector("#metrics-table tbody");
  body.innerHTML = data.validation.map(row => `<tr><td><b>${row.model}</b></td><td>${Number(row.roc_auc).toFixed(3)}</td><td>${fmt(row.average_precision)}</td><td>${fmt(row.recall)}</td><td>${fmt(row.f1)}</td><td>${Number(row.brier_score).toFixed(3)}</td></tr>`).join("");
}

function modelLabel(name) { return name === "lightgbm" || name === "lightgbm_optuna" ? "LightGBM" : name === "catboost" ? "CatBoost" : name === "xgboost" ? "XGBoost" : name === "knn" ? "KNN" : "Logistic Regression"; }
function trialLabel(name, candidate) { return `${modelLabel(name)} · Trial ${String(candidate.trial_id).split("-trial-")[1]}`; }
function parameterText(parameters) { return Object.entries(parameters).map(([key, value]) => `${key}=${value}`).join(" · "); }
function renderModelLab(data) {
  const summary = document.querySelector("#model-lab-summary");
  document.querySelector("#model-lab-results").hidden = false;
  const rows = [];
  summary.innerHTML = Object.entries(data.models).map(([name, payload]) => {
    const selected = payload.selected;
    const tuned = selected.validation_at_selected_threshold;
    const fixed = selected.validation_at_0_5;
    payload.candidates.forEach((candidate, index) => rows.push({name, index: index + 1, candidate}));
    return `<article class="model-card model-lab-selected"><h3>${modelLabel(name)}</h3><div><span>Selected threshold</span><b>${Number(tuned.threshold).toFixed(2)}</b></div><div><span>Validation F1 · tuned</span><b>${fmt(tuned.f1)}</b></div><div><span>Validation F1 · 0.50</span><b>${fmt(fixed.f1)}</b></div><small>${parameterText(selected.parameters)}</small></article>`;
  }).join("");
  document.querySelector("#model-lab-table tbody").innerHTML = rows.map(({name, index, candidate}) => {
    const cv = candidate.cross_validation;
    const selected = Object.entries(data.models[name].selected.parameters).every(([key, value]) => candidate.parameters[key] === value);
    return `<tr${selected ? ' class="selected-row"' : ""}><td>${candidate.rank}</td><td><b>${modelLabel(name)}</b><small>${candidate.trial_id}</small></td><td>${parameterText(candidate.parameters)}</td><td>${fmt(cv.average_precision)}</td><td>${fmt(candidate.cross_validation_std.average_precision)} std</td><td>${Number(cv.roc_auc).toFixed(3)}</td><td>${selected ? Number(candidate.selected_threshold).toFixed(2) : "—"}</td></tr>`;
  }).join("");
  const selectedModels = Object.entries(data.models).map(([name, payload]) => ({name, candidate: payload.candidates.find(candidate => candidate.selected)}));
  const best = selectedModels.reduce((winner, item) => item.candidate.cross_validation.average_precision > winner.candidate.cross_validation.average_precision ? item : winner);
  document.querySelector("#model-lab-conclusion").innerHTML = `<b>Current academic comparison:</b> ${modelLabel(best.name)} is the strongest selected candidate by train-CV Average Precision (${fmt(best.candidate.cross_validation.average_precision)}). This is a model-selection result for the defined metric, not an automatic production winner.`;
  document.querySelector("#journey-decision").textContent = `${modelLabel(best.name)} is currently strongest under train-CV Average Precision (${fmt(best.candidate.cross_validation.average_precision)}). The threshold is then reviewed on validation; this is an academic conclusion, not a production approval.`;
  const chartContainer = document.querySelector("#model-lab-chart");
  chartContainer.innerHTML = "";
  renderTrialComparisonChart(data.models);
  resizeCharts("#model-lab-chart");
}
function renderTrialComparisonChart(models) {
  const chartRows = Object.entries(models).flatMap(([name, payload]) => payload.candidates.map(candidate => ({name, candidate})));
  const apValues = chartRows.map(({candidate}) => candidate.cross_validation.average_precision);
  const bestAp = Math.max(...apValues);
  const minimumAp = Math.min(...apValues);
  const spread = Math.max(bestAp - minimumAp, 0.01);
  const modelColors = {logistic_regression: "#2563eb", lightgbm: "#0f766e", knn: "#94a3b8"};
  const labels = chartRows.map(({name, candidate}) => trialLabel(name, candidate));
  const annotations = chartRows.map(({name, candidate}, index) => ({
    x: candidate.cross_validation.average_precision,
    y: labels[index],
    xref: "x",
    yref: "y",
    text: candidate.selected ? `Selected · #${candidate.rank}` : `#${candidate.rank}`,
    showarrow: false,
    xanchor: "left",
    yanchor: "middle",
    xshift: 12,
    yshift: candidate.selected ? 12 : 8,
    font: {size: candidate.selected ? 11 : 10, color: candidate.selected ? "#172033" : "#607089", family: "Inter, ui-sans-serif, system-ui, sans-serif"}
  }));
  Plotly.newPlot("model-lab-chart", [{
    type: "scatter",
    mode: "markers",
    y: labels,
    x: apValues,
    error_x: {type: "data", array: chartRows.map(({candidate}) => candidate.cross_validation_std.average_precision), visible: true, color: "#94a3b8", thickness: 1, width: 4},
    marker: {size: chartRows.map(({candidate}) => candidate.selected ? 13 : 9), color: chartRows.map(({name, candidate}) => candidate.selected ? "#2563eb" : modelColors[name]), line: {width: 1, color: "#ffffff"}},
    customdata: chartRows.map(({name, candidate}) => [modelLabel(name), parameterText(candidate.parameters), candidate.cross_validation_std.average_precision, candidate.rank]),
    hovertemplate: "%{customdata[0]} · %{y}<br>CV AP: %{x:.2%} ± %{customdata[2]:.2%}<br>Rank: %{customdata[3]}<br>%{customdata[1]}<extra></extra>"
  }], {height: Math.max(520, chartRows.length * 38 + 100), margin:{l:205,r:150,t:24,b:66}, xaxis:{title:"Average Precision · train CV",tickformat:".1%",range:[Math.max(0, minimumAp - spread * 0.35), Math.min(1, bestAp + spread * 0.55)]}, yaxis:{autorange:"reversed",automargin:false}, annotations, showlegend:false}, plotConfig);
}
function renderHomeCredit(data) {
  document.querySelector("#home-credit-status").textContent=`${data.snapshot.rows.toLocaleString()} rows · ${readableTestStatus(data.test_status)}`;
  document.querySelector("#home-credit-summary").innerHTML=`<article class="model-card"><h3>Static snapshot</h3><div><span>Model features</span><b>${data.snapshot.features}</b></div><div><span>Entity-disjoint splits</span><b>${data.snapshot.train_rows.toLocaleString()} / ${data.snapshot.validation_rows.toLocaleString()} / ${data.snapshot.test_rows.toLocaleString()}</b></div></article><article class="model-card"><h3>Policy evidence</h3><div><span>Review capacities</span><b>1% · 5% · 10% · 20%</b></div><div><span>Primary selection metric</span><b>Train-CV Average Precision</b></div><div><span>Test status</span><b>${data.test_status}</b></div></article>`;
  const atTen=Object.fromEntries(data.policy.models?Object.entries(data.policy.models).map(([name,rows])=>[name,rows.find(row=>Number(row.capacity)===.1)]):[]);
  document.querySelector("#home-credit-table tbody").innerHTML=data.models.map(row=>{const policy=atTen[row.model]||{};const metric=row.validation;return `<tr><td><b>${modelLabel(row.model)}</b></td><td>${row.selected_trial}</td><td>${fmt(row.cv_average_precision)}</td><td>${fmt(metric.average_precision)}</td><td>${Number(metric.roc_auc).toFixed(3)}</td><td>${fmt(policy.precision_at_capacity||0)}</td><td>${fmt(policy.recall_at_capacity||0)}</td></tr>`;}).join("");
  document.querySelector("#home-credit-policy-cards").innerHTML=Object.entries(atTen).map(([name,row])=>`<article class="model-card"><h3>${modelLabel(name)} · 10% review</h3><div><span>Cases reviewed</span><b>${row.reviewed_rows.toLocaleString()}</b></div><div><span>Precision@capacity</span><b>${fmt(row.precision_at_capacity)}</b></div><div><span>Recall@capacity</span><b>${fmt(row.recall_at_capacity)}</b></div><div><span>Lift</span><b>${Number(row.lift).toFixed(2)}×</b></div></article>`).join("");
  document.querySelector("#home-credit-limitation").textContent=`${data.note} ${data.limitation}`;
}
let homeEdaLoaded = false;
function renderHomeEda(data) {
  const status = document.querySelector("#home-eda-status");
  status.textContent = "Cached EDA loaded · train analysis · test unopened";
  status.className = "pill";
  const snapshot = data.prevalence.snapshot;
  const validation = data.prevalence.validation;
  document.querySelector("#home-eda-summary").innerHTML=`<span><b>${fmt(snapshot.rate)}</b> snapshot target rate</span><span><b>${fmt(validation.rate)}</b> validation target rate</span><span><b>${Number(data.population.train_rows).toLocaleString()}</b> train rows analyzed</span><span><b>${data.correlations.features.length}</b> correlation features</span>`;
  document.querySelector("#home-eda-limitation").textContent=`${data.limitations.join(" ")} Audit-only columns: ${data.audit_only.columns.join(" · ")}.`;
  Plotly.newPlot("home-eda-prevalence-chart", [{type:"bar",x:["Snapshot","Validation"],y:[snapshot.rate,validation.rate],text:[fmt(snapshot.rate),fmt(validation.rate)],textposition:"outside",marker:{color:[chartColors.reference,chartColors.logistic_regression]},hovertemplate:"%{x}<br>Observed target rate: %{y:.2%}<extra></extra>"}],{height:285,margin:{l:65,r:20,t:30,b:60},xaxis:{title:"Population"},yaxis:{title:"Observed target rate",range:[0,Math.min(1,Math.max(snapshot.rate,validation.rate)*1.45)],tickformat:".1%",gridcolor:"#e7edf5"},showlegend:false},plotConfig);
  const missing = data.missingness.features.slice(0,12).reverse();
  Plotly.newPlot("home-eda-missingness-chart", [{type:"bar",orientation:"h",y:missing.map(row=>row.feature),x:missing.map(row=>row.missing_rate),text:missing.map(row=>fmt(row.missing_rate)),textposition:"outside",marker:{color:"#94a3b8"},hovertemplate:"%{y}<br>Missing: %{x:.2%}<br>Cases: %{customdata:,}<extra></extra>",customdata:missing.map(row=>row.missing_cases)}],{height:Math.max(330,missing.length*28),margin:{l:165,r:65,t:25,b:58},xaxis:{title:"Missing rate",range:[0,Math.max(.01,missing[missing.length-1]?.missing_rate*1.2||.01)],tickformat:".0%",gridcolor:"#e7edf5"},yaxis:{autorange:"reversed",automargin:true,showgrid:false},showlegend:false},plotConfig);
  const contrasts=data.distributions.features.filter(row=>row.contrast.iqr_scaled_difference!==null); const contrastColors=contrasts.map(row=>row.contrast.iqr_scaled_difference>=0?chartColors.logistic_regression:"#b42318");
  Plotly.newPlot("home-eda-distribution-chart", [{type:"scatter",mode:"markers+text",x:contrasts.map(row=>row.contrast.iqr_scaled_difference),y:contrasts.map(row=>row.feature),text:contrasts.map(row=>`${row.contrast.iqr_scaled_difference>=0?"+":""}${Number(row.contrast.iqr_scaled_difference).toFixed(2)}×`),textposition:"middle right",cliponaxis:false,marker:{size:10,color:contrastColors,line:{width:1,color:"#fff"}},customdata:contrasts.map(row=>[row.by_target["0"].median,row.by_target["1"].median,row.contrast.iqr]),hovertemplate:"%{y}<br>Median TARGET 0: %{customdata[0]:.3g}<br>Median TARGET 1: %{customdata[1]:.3g}<br>Median difference / IQR: %{x:.2f}×<extra></extra>"}],{height:Math.max(330,contrasts.length*28),margin:{l:175,r:65,t:25,b:70},xaxis:{title:"Median difference · TARGET 1 minus TARGET 0, scaled by feature IQR",zeroline:true,zerolinecolor:"#64748b",gridcolor:"#e7edf5"},yaxis:{autorange:"reversed",automargin:true,showgrid:false},showlegend:false},plotConfig);
  const correlation=data.correlations; Plotly.newPlot("home-eda-correlation-chart", [{type:"heatmap",z:correlation.matrix,x:correlation.features,y:correlation.features,zmin:-1,zmax:1,colorscale:[[0,"#b42318"],[.5,"#f8fafc"],[1,"#2563eb"]],text:correlation.matrix.map(row=>row.map(value=>Number(value).toFixed(2))),texttemplate:"%{text}",hovertemplate:"%{y} × %{x}<br>Pearson correlation: %{z:.2f}<extra></extra>",colorbar:{title:"r",tickformat:".1f"}}],{height:Math.max(480,correlation.features.length*31),margin:{l:180,r:30,t:20,b:175},xaxis:{tickangle:-45,automargin:true},yaxis:{autorange:"reversed",automargin:true},showlegend:false},plotConfig);
  document.querySelector("#home-eda-contract").innerHTML=`<div><span>Dataset fingerprint</span><b class="mono">${String(data.reproducibility.dataset_fingerprint).slice(0,12)}…</b></div><div><span>Feature version</span><b class="mono">${data.feature_version}</b></div><div><span>Analysis population</span><b>${data.population.analysis_split}</b></div><div><span>Final test</span><b>${data.test_status}</b></div><div><span>Correlation method</span><b>${data.reproducibility.correlation_method}</b></div><div><span>Audit-only fields</span><b>${data.audit_only.columns.length} excluded</b></div>`;
}
async function loadHomeEda() { if(homeEdaLoaded) return; try { renderHomeEda(await api("/api/home-credit/eda")); homeEdaLoaded=true; } catch(error) { const status=document.querySelector("#home-eda-status"); status.className="pill is-error"; status.textContent=`EDA unavailable: ${error.message}`; document.querySelector("#home-eda-limitation").textContent="The cached EDA report is unavailable. Run the offline materialization job before opening this tab."; ["#home-eda-summary","#home-eda-prevalence-chart","#home-eda-missingness-chart","#home-eda-distribution-chart","#home-eda-correlation-chart","#home-eda-contract"].forEach(selector=>{const element=document.querySelector(selector); if(element) element.innerHTML="Cached EDA evidence unavailable.";}); } }
function setupHomeViewTabs() { document.querySelectorAll(".home-view-tab").forEach(button=>button.addEventListener("click",()=>{const target=button.getAttribute("aria-controls"); document.querySelectorAll(".home-view-tab").forEach(item=>{const active=item===button; item.classList.toggle("is-active",active); item.setAttribute("aria-selected",String(active));}); document.querySelectorAll("#home-story-view,#home-eda-view").forEach(panel=>{panel.hidden=panel.id!==target;}); if(target==="home-eda-view") loadHomeEda();})); }
function homeAcademicCopy() {
  if (document.documentElement.lang === "es") return {loaded:"Evidencia académica cargada · se conservan los límites de validation y test.",reproTitle:"Contrato de reproducibilidad",splitSeed:"Seed del split",experimentSeed:"Seed del experimento",folds:"Folds de cross-validation",featureVersion:"Versión de features",fingerprint:"Fingerprint del dataset",reproExplanation:"El seed hace repetible el experimento; no hace más preciso al modelo. La confianza se obtiene comprobando la estabilidad entre folds y futuros seeds.",featureComparisonTitle:"¿Las nuevas features mejoraron el modelo?",featureComparisonUnavailable:"La comparación v2 todavía no está disponible.",ablationTitle:"¿Qué familia aporta más?",ablationUnavailable:"La ablación de familias todavía no está disponible.",benchmarkTitle:"¿Cómo se eligió el candidato clásico?",benchmarkUnavailable:"El benchmark clásico todavía no está disponible.",benchmarkExplanation:"Optuna busca parámetros dentro de train-CV; validation sólo comprueba la selección. CatBoost y XGBoost son challengers fijos. Ningún modelo se promociona automáticamente.",neuralTitle:"¿Añade evidencia una red neuronal?",neuralUnavailable:"El benchmark neural todavía no está disponible. Ejecuta el CLI offline para materializarlo.",neuralExplanation:"La red aprende una relación no lineal, pero su complejidad no demuestra superioridad. El holdout interno decide cuándo parar; validation sólo se consulta al final.",featureCount:"features",baseline:"Baseline",challenger:"Challenger",featureExplanation:"La comparación mantiene el split y la métrica; sólo cambia la versión de features.",ablationExplanation:"Cada punto añade una familia al baseline; no es una prueba causal.",iterationImproved:"mejoró el AP de train-CV desde",iterationTo:"hasta",iterationSelected:"fue seleccionado con AP de train-CV",splitLabels:["Train","Validation","Test"],overall:"prevalencia total del target",validation:"prevalencia en validation",test:"estado del test",contextChartLabel:"Prevalencia del target en el snapshot y validation",contextChartAxis:"Tasa observada del target",testUnopened:"reservado para la evaluación final",testExplanation:"El test permanece sin abrir: no se usa para elegir parámetros, umbrales ni modelos.",featureLabels:{application:"Datos de solicitud",bureau:"Agregados de bureau",previous_application:"Agregados de solicitudes previas",installments:"Agregados de pagos de cuotas"},featureExplanations:{application:"Valores de la tabla de solicitudes en el snapshot estático.",bureau:"Conteos y saldos agregados desde la tabla bureau.",previous_application:"Conteos e importes históricos agregados por entidad.",installments:"Conteos de pagos, retrasos, faltantes e importes agregados."},audit:"Campos audit-only excluidos de las entradas del modelo",selected:"Trial seleccionado",validationAp:"AP en validation",validationRoc:"ROC-AUC en validation",calibration:"Evidencia de calibración",futureTitle:"Futuras iteraciones del modelo",futureCopy:"Los nuevos candidatos deben añadir parámetros, split de ajuste, métrica primaria, resultado de validation y decisión.",currentTest:"Estado del test"};
  return {loaded:"Academic evidence loaded · validation and test boundaries preserved.",reproTitle:"Reproducibility contract",splitSeed:"Split seed",experimentSeed:"Experiment seed",folds:"Cross-validation folds",featureVersion:"Feature version",fingerprint:"Dataset fingerprint",reproExplanation:"The seed makes the experiment repeatable; it does not make the model more accurate. Confidence comes from checking stability across folds and future seeds.",featureComparisonTitle:"Did the new features improve the model?",featureComparisonUnavailable:"The v2 feature comparison is not available yet.",ablationTitle:"Which feature family contributes most?",ablationUnavailable:"The feature-family ablation is not available yet.",benchmarkTitle:"How was the classical candidate selected?",benchmarkUnavailable:"The classical benchmark is not available yet.",benchmarkExplanation:"Optuna searches parameters inside train-CV; validation only checks the selected candidate. CatBoost and XGBoost are fixed challengers. No model is promoted automatically.",neuralTitle:"Does a neural network add evidence?",neuralUnavailable:"The neural benchmark is not available yet. Run the offline CLI to materialize it.",neuralExplanation:"The network learns a nonlinear relationship, but complexity is not evidence of superiority. The internal holdout decides when to stop; validation is checked only at the end.",featureCount:"features",baseline:"Baseline",challenger:"Challenger",featureExplanation:"The comparison keeps the split and metric unchanged; only the feature version changes.",ablationExplanation:"Each point adds one family to the baseline; it is not a causal test.",iterationImproved:"improved train-CV AP from",iterationTo:"to",iterationSelected:"was selected with train-CV AP",splitLabels:["Train","Validation","Test"],overall:"overall target prevalence",validation:"validation prevalence",test:"final test status",contextChartLabel:"Target prevalence in the snapshot and validation split",contextChartAxis:"Observed target rate",testUnopened:"reserved for final evaluation",testExplanation:"The test remains unopened: it is not used to choose parameters, thresholds, or models.",featureLabels:{},featureExplanations:{},audit:"Audit-only fields excluded from model inputs",selected:"Selected trial",validationAp:"Validation AP",validationRoc:"Validation ROC-AUC",calibration:"Calibration evidence",futureTitle:"Future model iterations",futureCopy:"New candidates should be appended with parameters, fit split, primary metric, validation result, and a decision.",currentTest:"Test status"};
}
function renderHomeAcademic(data) {
  state.homeAcademic = data;
  const copy = homeAcademicCopy();
  const homePlot = (...args) => Plotly.newPlot(...args);
  document.querySelector("#home-academic-status").textContent=copy.loaded;
  document.querySelector("#home-academic-status").className="lab-status";
  const splitLabels = copy.splitLabels;
  const splitValues = [data.evidence_boundary.split_rows.train, data.evidence_boundary.split_rows.validation, data.evidence_boundary.split_rows.test];
  homePlot("home-split-chart", [{type:"bar", x:splitLabels, y:splitValues, marker:{color:[chartColors.logistic_regression,chartColors.lightgbm,chartColors.reference]}, text:splitValues.map(value=>value.toLocaleString(document.documentElement.lang)), textposition:"auto", hovertemplate:"%{x}<br>%{y:,} rows<extra></extra>"}], {height:300,margin:{l:70,r:20,t:20,b:58},xaxis:{title:"Evidence split",showgrid:false},yaxis:{title:"Rows",tickformat:",",rangemode:"tozero",gridcolor:"#e7edf5",zerolinecolor:"#b7c4d6"},showlegend:false}, plotConfig);
  document.querySelector("#home-data-summary").innerHTML=`<span><b>${(data.dataset.overall_prevalence*100).toFixed(1)}%</b> ${copy.overall}</span><span><b>${(data.dataset.validation_prevalence*100).toFixed(1)}%</b> ${copy.validation}</span><span><b>${data.evidence_boundary.test_status}</b> ${copy.test}</span>`;
  const reproducibility = data.reproducibility;
  document.querySelector("#home-reproducibility").innerHTML=`<h3>${copy.reproTitle}</h3><div class="reproducibility-grid"><div class="metadata-cell"><span class="metadata-label">${copy.splitSeed}</span><b class="metadata-value mono">${reproducibility.split_seed}</b></div><div class="metadata-cell"><span class="metadata-label">${copy.experimentSeed}</span><b class="metadata-value mono">${reproducibility.experiment_seed}</b></div><div class="metadata-cell"><span class="metadata-label">${copy.folds}</span><b class="metadata-value">${reproducibility.cross_validation_folds}</b></div><div class="metadata-cell"><span class="metadata-label">${copy.featureVersion}</span><b class="metadata-value mono">${reproducibility.feature_version}</b></div><div class="metadata-cell"><span class="metadata-label">${copy.fingerprint}</span><b class="metadata-value mono">${String(reproducibility.dataset_fingerprint).slice(0,12)}…</b></div></div><span>${copy.reproExplanation}</span>`;
  document.querySelector("#home-feature-groups").innerHTML=data.feature_groups.map(group=>`<article class="feature-story-card"><span>${group.source_tables.join(" · ")}</span><h3>${copy.featureLabels[group.id]||group.label}</h3><b>${group.features.length} features</b><p>${copy.featureExplanations[group.id]||group.explanation}</p><small class="feature-identifiers">${group.features.join(" · ")}</small></article>`).join("");
  const featureComparison = data.feature_comparison;
  document.querySelector("#home-feature-comparison").innerHTML=featureComparison.status!=="available"?`<h3>${copy.featureComparisonTitle}</h3><span>${copy.featureComparisonUnavailable}</span>`:`<h3>${copy.featureComparisonTitle}</h3><div class="reproducibility-grid"><div class="metadata-cell"><span class="metadata-label">${copy.baseline}</span><b class="metadata-value mono">${featureComparison.baseline_feature_version} · ${featureComparison.baseline_feature_count} ${copy.featureCount}</b></div><div class="metadata-cell"><span class="metadata-label">${copy.challenger}</span><b class="metadata-value mono">${featureComparison.challenger_feature_version} · ${featureComparison.challenger_feature_count} ${copy.featureCount}</b></div>${featureComparison.models.map(model=>`<div class="metadata-cell"><span class="metadata-label">${modelLabel(model.model)} · validation AP</span><b class="metadata-value"><span class="comparison-old">${fmt(model.baseline_validation_average_precision)}</span><span aria-hidden="true"> → </span><span class="comparison-new">${fmt(model.challenger_validation_average_precision)}</span></b></div>`).join("")}</div><span>${copy.featureExplanation} ${featureComparison.human_explanation}</span>`;
  const ablation = featureComparison.ablation;
  if (ablation.status === "available") { const rows=Object.entries(ablation.results).map(([name,result])=>({name,result})); const values=rows.map(row=>row.result.validation.average_precision); const minimum=Math.min(...values); const maximum=Math.max(...values); const padding=Math.max((maximum-minimum)*.35,.0025); const range=[Math.max(0,minimum-padding),Math.min(1,maximum+padding)]; homePlot("home-feature-ablation-chart",[{type:"scatter",mode:"markers+text",orientation:"h",y:rows.map(row=>row.name),x:values,text:values.map(value=>fmt(value)),textposition:"middle right",cliponaxis:false,marker:{size:11,color:rows.map(row=>row.name==="all_v2"?"#2563eb":"#94a3b8"),line:{width:1,color:"#fff"}},customdata:rows.map(row=>[row.result.feature_count,row.result.cross_validation.average_precision,row.result.cross_validation_std.average_precision]),hovertemplate:"%{y}<br>Validation AP: %{x:.2%}<br>Features: %{customdata[0]}<br>Train-CV AP: %{customdata[1]:.2%} ± %{customdata[2]:.2%}<extra></extra>"}],{height:Math.max(300,rows.length*45),margin:{l:170,r:75,t:58,b:70},xaxis:{title:"Validation Average Precision · zoomed comparison",range, tickformat:".2%",gridcolor:"#e7edf5",zeroline:false},yaxis:{autorange:"reversed",automargin:true,showgrid:false},title:copy.ablationTitle,showlegend:false,annotations:[{text:"Zoomed scale · exact values shown",xref:"paper",yref:"paper",x:.5,y:1.12,showarrow:false,font:{size:11,color:"#64748b"}}]},plotConfig); } else document.querySelector("#home-feature-ablation-chart").innerHTML=copy.ablationUnavailable;
  document.querySelector("#home-audit-only").textContent=`${copy.audit}: ${data.audit_only.columns.join(" · ")}. ${data.audit_only.explanation}`;
  const iterations = data.iterations;
  const modelColors = chartColors;
  homePlot("home-trial-chart", [{type:"scatter",mode:"markers+text",x:iterations.map(item=>item.cross_validation.average_precision),y:iterations.map(item=>`${modelLabel(item.model)} · ${item.iteration_id.split("-trial-")[1]}`),text:iterations.map(item=>item.selected?"Selected":""),textposition:"middle right",error_x:{type:"data",array:iterations.map(item=>item.cross_validation_std.average_precision),visible:true},marker:{size:iterations.map(item=>item.selected?15:9),color:iterations.map(item=>item.selected?"#111827":modelColors[item.model]),opacity:iterations.map(item=>item.selected?1:.68),line:{width:1,color:"#fff"}},customdata:iterations.map(item=>[item.cross_validation_std.average_precision,parameterText(item.parameters),item.rank,item.model,item.selected]),hovertemplate:"%{y}<br>CV Average Precision: %{x:.2%} ± %{customdata[0]:.2%}<br>Parameters: %{customdata[1]}<br>Rank: %{customdata[2]}<br>Model: %{customdata[3]}<extra></extra>"}], {height:Math.max(310,iterations.length*42),margin:{l:150,r:45,t:20,b:70},xaxis:{title:"Train-CV Average Precision",tickformat:".1%"},yaxis:{autorange:"reversed",automargin:true},showlegend:false}, plotConfig);
  const benchmark = data.classical_benchmark;
  const benchmarkElement = document.querySelector("#home-classical-benchmark");
  if (benchmark.status !== "available") benchmarkElement.innerHTML=`<h3>${copy.benchmarkTitle}</h3><span>${copy.benchmarkUnavailable}</span>`;
  else {
    const benchmarkRows = benchmark.models.filter(row => row.status === "available");
    benchmarkElement.innerHTML=`<h3>${copy.benchmarkTitle}</h3><div class="benchmark-meta"><div><span>Selection</span><b>${benchmark.selection_split}</b></div><div><span>Metric</span><b>${benchmark.primary_metric}</b></div><div><span>Seed · folds</span><b>${benchmark.experiment_seed} · ${benchmark.cross_validation_folds}</b></div></div><div class="benchmark-results">${benchmarkRows.map(row=>`<div class="benchmark-result"><span>${modelLabel(row.model)} · ${row.search}</span><b>${row.validation_average_precision === null ? "—" : fmt(row.validation_average_precision)} validation AP</b></div>`).join("")}</div><span>${copy.benchmarkExplanation} ${benchmark.human_explanation}</span>`;
    const chartRows = benchmarkRows.filter(row => row.validation_average_precision !== null);
    if (chartRows.length) homePlot("home-classical-benchmark-chart", [{type:"scatter",mode:"markers+text",x:chartRows.map(row=>row.validation_average_precision),y:chartRows.map(row=>modelLabel(row.model)),text:chartRows.map(row=>fmt(row.validation_average_precision)),textposition:"middle right",marker:{size:12,color:"#2563eb",line:{width:1,color:"#fff"}},customdata:chartRows.map(row=>[row.cross_validation_average_precision,row.cross_validation_std?.average_precision ?? null,row.search]),hovertemplate:"%{y}<br>Validation AP: %{x:.2%}<br>Train-CV AP: %{customdata[0]:.2%}<br>Search: %{customdata[2]}<extra></extra>"}],{height:300,margin:{l:150,r:35,t:20,b:65},xaxis:{title:"Validation Average Precision · 20–30% view",range:[.20,.30],tickformat:".1%",gridcolor:"#e7edf5"},yaxis:{title:"Classical candidate",autorange:"reversed",automargin:true,showgrid:false},showlegend:false},plotConfig);
  }
  const neural = data.deep_learning;
  const neuralElement = document.querySelector("#home-deep-learning");
  if (neural.status !== "available") {
    neuralElement.innerHTML=`<h3>${copy.neuralTitle}</h3><span>${copy.neuralUnavailable}</span>`;
  } else {
    neuralElement.innerHTML=`<h3>${copy.neuralTitle}</h3><div class="reproducibility-grid"><div class="metadata-cell"><span class="metadata-label">Architecture</span><b class="metadata-value mono">${neural.architecture.join(" → ")}</b></div><div class="metadata-cell"><span class="metadata-label">Parameters</span><b class="metadata-value">${Number(neural.parameter_count).toLocaleString()}</b></div><div class="metadata-cell"><span class="metadata-label">Features</span><b class="metadata-value">${neural.raw_feature_count} raw · ${neural.encoded_feature_count} encoded</b></div><div class="metadata-cell"><span class="metadata-label">Best epoch</span><b class="metadata-value">${neural.best_epoch} / ${neural.hyperparameters.epochs_completed}</b></div><div class="metadata-cell"><span class="metadata-label">Stopping</span><b class="metadata-value">${neural.early_stopping_split}</b></div><div class="metadata-cell"><span class="metadata-label">Validation AP</span><b class="metadata-value">${fmt(neural.validation.average_precision)}</b></div></div><span>${copy.neuralExplanation} ${neural.human_explanation}</span>`;
    const history = neural.learning_curve;
  homePlot("home-deep-learning-chart", [{type:"scatter",mode:"lines+markers",name:"Train loss",x:history.map(row=>row.epoch),y:history.map(row=>row.train_loss),line:{color:"#2563eb"},hovertemplate:"Epoch %{x}<br>Train loss: %{y:.4f}<extra></extra>"},{type:"scatter",mode:"lines+markers",name:"Early-stop AP",x:history.map(row=>row.epoch),y:history.map(row=>row.early_stopping_average_precision),yaxis:"y2",line:{color:"#f59e0b"},hovertemplate:"Epoch %{x}<br>Train-holdout AP: %{y:.2%}<extra></extra>"}],{height:320,margin:{l:65,r:65,t:24,b:75},xaxis:{title:"Epoch"},yaxis:{title:"Weighted loss"},yaxis2:{title:"Train-holdout AP",overlaying:"y",side:"right",range:[0,1],tickformat:".0%"},legend:{orientation:"h",x:.5,y:-.25,xanchor:"center",yanchor:"top"}},plotConfig);
    const comparison = (neural.classical_comparison.models || []).map(row=>({model:modelLabel(row.model),ap:row.validation_average_precision}));
    comparison.push({model:"MLP",ap:neural.validation.average_precision});
    homePlot("home-deep-learning-comparison",[{type:"scatter",mode:"markers+text",x:comparison.map(row=>row.ap),y:comparison.map(row=>row.model),text:comparison.map(row=>fmt(row.ap)),textposition:"middle right",marker:{size:12,color:comparison.map(row=>row.model==="MLP"?chartColors.mlp:chartColors.reference),line:{width:1,color:"#fff"}},hovertemplate:"%{y}<br>Validation AP: %{x:.2%}<extra></extra>"}],{height:300,margin:{l:150,r:35,t:24,b:65},xaxis:{title:"Validation Average Precision · 20–30% view",range:[.20,.30],tickformat:".1%",gridcolor:"#e7edf5"},yaxis:{title:"Candidate",autorange:"reversed",automargin:true,showgrid:false},showlegend:false},plotConfig);
  }
  document.querySelector("#home-iteration-result").innerHTML=data.models.map(model=>{const comparison=model.iteration_comparison; const firstAp=Number(comparison.baseline_average_precision); const selectedAp=Number(comparison.selected_average_precision); const copyText=Number(comparison.average_precision_delta)>0?`${modelLabel(model.model)} · ${comparison.selected_trial} ${copy.iterationImproved} ${fmt(firstAp)} ${copy.iterationTo} ${fmt(selectedAp)}.`:`${modelLabel(model.model)} · ${comparison.selected_trial} ${copy.iterationSelected} ${fmt(selectedAp)}.`; return `<span class="iteration-result-line">${copyText}</span>`;}).join("");
  document.querySelector("#home-iteration-table tbody").innerHTML=iterations.map(item=>`<tr${item.selected?` class="selected-row"`:``}><td>${modelLabel(item.model)}</td><td>${item.iteration_id}</td><td>${parameterText(item.parameters)}</td><td>${fmt(item.cross_validation.average_precision)}</td><td>${fmt(item.cross_validation_std.average_precision)}</td><td>${item.rank}</td><td>${item.validation?fmt(item.validation.average_precision):"—"}</td></tr>`).join("");
  document.querySelector("#home-iteration-summary").innerHTML=data.models.map(model=>`<article class="model-card"><h3>${modelLabel(model.model)}</h3><div><span>${copy.selected}</span><b>${model.selected_trial}</b></div><div><span>${copy.validationAp}</span><b>${fmt(model.selected_validation.average_precision)}</b></div><div><span>${copy.validationRoc}</span><b>${Number(model.selected_validation.roc_auc).toFixed(3)}</b></div></article>`).join("");
  const selectedValidation = data.models.map(model=>({model:modelLabel(model.model),metrics:model.selected_validation}));
  homePlot("home-validation-chart", [{type:"bar",name:"Average Precision",x:selectedValidation.map(row=>row.model),y:selectedValidation.map(row=>row.metrics.average_precision),marker:{color:chartColors.precision},hovertemplate:"%{x}<br>Average Precision: %{y:.2%}<extra></extra>"},{type:"bar",name:"ROC-AUC",x:selectedValidation.map(row=>row.model),y:selectedValidation.map(row=>row.metrics.roc_auc),marker:{color:chartColors.f1},hovertemplate:"%{x}<br>ROC-AUC: %{y:.3f}<extra></extra>"},{type:"bar",name:"Brier score · lower is better",x:selectedValidation.map(row=>row.model),y:selectedValidation.map(row=>row.metrics.brier_score),yaxis:"y2",marker:{color:chartColors.warning},hovertemplate:"%{x}<br>Brier score: %{y:.3f}<extra></extra>"},{type:"bar",name:"Log loss · lower is better",x:selectedValidation.map(row=>row.model),y:selectedValidation.map(row=>row.metrics.log_loss),yaxis:"y2",marker:{color:"#b42318"},hovertemplate:"%{x}<br>Log loss: %{y:.3f}<extra></extra>"}], {height:350,margin:{l:60,r:70,t:24,b:88},barmode:"group",xaxis:{title:"Selected candidate"},yaxis:{title:"Ranking metrics",range:[0,1]},yaxis2:{title:"Probability error",overlaying:"y",side:"right",range:[0,.35]},legend:{orientation:"h",x:.5,y:-.25,xanchor:"center",yanchor:"top"}}, plotConfig);
  const calibrationColors = chartColors;
  const calibrationTraces = data.calibration.models.map(model=>({type:"scatter",mode:"lines+markers",name:modelLabel(model.model),x:model.points.map(point=>point.mean_predicted_probability),y:model.points.map(point=>point.observed_default_rate),customdata:model.points.map(point=>[point.cases,point.bin_lower,point.bin_upper]),line:{color:calibrationColors[model.model]},hovertemplate:`${modelLabel(model.model)}<br>Mean predicted: %{x:.1%}<br>Observed rate: %{y:.1%}<br>Cases: %{customdata[0]}<extra></extra>`}));
  homePlot("home-calibration-chart",calibrationTraces.concat([{type:"scatter",mode:"lines",name:"Perfect calibration",x:[0,1],y:[0,1],line:{color:"#94a3b8",dash:"dot"},hoverinfo:"skip"}]),{height:330,margin:{l:65,r:18,t:20,b:88},xaxis:{title:"Mean predicted probability",range:[0,1],tickformat:".0%"},yaxis:{title:"Observed target rate",range:[0,1],tickformat:".0%"},legend:{orientation:"h",x:.5,y:-.25,xanchor:"center",yanchor:"top"}},plotConfig);
  document.querySelector("#home-calibration-note").textContent=`${copy.calibration}: ${data.calibration.status}. ${data.calibration.reason}`;
  const policyRows = Object.entries(data.policy.models).flatMap(([name,rows])=>rows.map(row=>({...row,model:name})));
  const capacities = [...new Set(policyRows.map(row=>Number(row.capacity)))].sort((a,b)=>a-b);
  const policyTraces = Object.entries(data.policy.models).flatMap(([name,rows])=>[{type:"scatter",mode:"lines+markers",name:`${modelLabel(name)} · precision`,x:rows.map(row=>Number(row.capacity)),y:rows.map(row=>row.precision_at_capacity),line:{color:modelColors[name]},marker:{symbol:"circle"},hovertemplate:`${modelLabel(name)} precision<br>Capacity: %{x:.0%}<br>Value: %{y:.1%}<extra></extra>`},{type:"scatter",mode:"lines+markers",name:`${modelLabel(name)} · recall`,x:rows.map(row=>Number(row.capacity)),y:rows.map(row=>row.recall_at_capacity),line:{color:modelColors[name],dash:"dot"},marker:{symbol:"diamond"},hovertemplate:`${modelLabel(name)} recall<br>Capacity: %{x:.0%}<br>Value: %{y:.1%}<extra></extra>`}]);
  homePlot("home-policy-chart",policyTraces,{height:360,margin:{l:65,r:18,t:20,b:95},xaxis:{title:"Available review capacity",tickformat:".0%",tickvals:capacities},yaxis:{title:"Proportion",range:[0,1],tickformat:".0%"},legend:{orientation:"h",x:.5,y:-.28,xanchor:"center",yanchor:"top"},shapes:[{type:"line",x0:.1,x1:.1,y0:0,y1:1,yref:"paper",line:{dash:"dash",color:"#111827",width:1.2},opacity:.65}],annotations:[{x:.1,y:1.03,xref:"x",yref:"paper",text:"Current 10% reference",showarrow:false,font:{size:11}}]},plotConfig);
  const liftTraces = Object.entries(data.policy.models).map(([name,rows])=>({type:"scatter",mode:"lines+markers",name:modelLabel(name),x:rows.map(row=>Number(row.capacity)),y:rows.map(row=>row.lift),line:{color:modelColors[name]},hovertemplate:`${modelLabel(name)}<br>Capacity: %{x:.0%}<br>Lift: %{y:.2f}×<extra></extra>`}));
  homePlot("home-policy-lift-chart",liftTraces,{height:290,margin:{l:65,r:18,t:20,b:70},xaxis:{title:"Available review capacity",tickformat:".0%",tickvals:capacities},yaxis:{title:"Lift vs prevalence",rangemode:"tozero"},showlegend:false},plotConfig);
  const best = data.models.reduce((winner,item)=>item.selected_validation.average_precision>winner.selected_validation.average_precision?item:winner,data.models[0]);
  document.querySelector("#home-academic-conclusion").textContent=document.documentElement.lang === "es"?`${modelLabel(best.model)} es el candidato seleccionado más fuerte según Average Precision en validation (${fmt(best.selected_validation.average_precision)}). Esta conclusión queda limitada al protocolo estático; no es una promoción ni una aprobación productiva.`:`${modelLabel(best.model)} is the strongest selected candidate under validation Average Precision (${fmt(best.selected_validation.average_precision)}). This conclusion is bounded to the static validation protocol; it is not a promotion or production approval.`;
  const testStatus = data.test_status === "unopened" ? copy.testUnopened : data.test_status;
  document.querySelector("#home-iteration-contract").innerHTML=`<h3>${copy.futureTitle}</h3><p>${copy.futureCopy} ${document.documentElement.lang === "es"?"El contrato actual exige":"The current contract requires"}: ${data.future_iteration_contract.required_fields.join(" · ")}.</p><span class="pill">${copy.currentTest}: ${testStatus}</span><p class="technical-note">${copy.testExplanation}</p>`;
}
function setupHomeStoryMotion() { const chapters=[...document.querySelectorAll("[data-story-chapter]")]; const links=[...document.querySelectorAll(".home-story-nav a")]; if(!chapters.length) return; if(!("IntersectionObserver" in window)) { chapters.forEach(chapter=>chapter.classList.add("is-visible")); return; } const observer=new IntersectionObserver(entries=>entries.forEach(entry=>{if(!entry.isIntersecting) return; entry.target.classList.add("is-visible"); links.forEach(link=>{const active=link.getAttribute("href")===`#${entry.target.id}`; link.classList.toggle("is-active",active); if(active) link.setAttribute("aria-current","step"); else link.removeAttribute("aria-current");});}),{rootMargin:"-25% 0px -55% 0px",threshold:.01}); chapters.forEach(chapter=>observer.observe(chapter)); }
async function loadHomeCredit() { try { renderHomeCredit(await api("/api/home-credit")); } catch(error) { document.querySelector("#home-credit-status").textContent="Report unavailable"; document.querySelector("#home-credit-limitation").textContent=`Build the static snapshot and baseline to enable this panel: ${error.message}`; } try { renderHomeAcademic(await api("/api/home-credit/academic")); } catch(error) { const status=document.querySelector("#home-academic-status"); status.className="lab-status is-error"; status.textContent=`Academic evidence unavailable: ${error.message}`; ["#home-split-chart","#home-reproducibility","#home-feature-groups","#home-feature-comparison","#home-feature-ablation-chart","#home-trial-chart","#home-classical-benchmark","#home-classical-benchmark-chart","#home-deep-learning","#home-deep-learning-chart","#home-deep-learning-comparison","#home-iteration-result","#home-iteration-summary","#home-iteration-table tbody","#home-validation-chart","#home-calibration-chart","#home-policy-chart","#home-policy-lift-chart"].forEach(selector=>{const element=document.querySelector(selector); if(element) element.innerHTML="Academic evidence unavailable.";}); document.querySelector("#home-academic-conclusion").textContent="Academic evidence could not be loaded."; document.querySelector("#home-calibration-note").textContent="Academic evidence could not be loaded."; } }
let uciLoaded = false;
async function loadUciReference() {
  if (uciLoaded) return;
  try {
    await setupExamples();
    const [overview,metrics,roc,probabilities,calibration]=await Promise.all([api("/api/overview"),api("/api/metrics"),api("/api/roc"),api("/api/probabilities"),api("/api/calibration")]);
    document.querySelector("#run-id").textContent=`Run ${overview.run_id}`;
    renderMetrics(metrics); renderRoc(roc); renderProbabilities(probabilities); renderCalibration(calibration);
    setupThreshold(); setupCapacity(); setupModelLab(); buildForm();
    uciLoaded = true;
    resizeUciCharts();
  } catch(error) {
    document.querySelector("#tab-uci").innerHTML=`<div class="panel"><h2>Could not load the UCI reference</h2><p>${error.message}</p></div>`;
  }
}
function persistDataset(target) {
  const url = new URL(window.location.href);
  url.searchParams.set("dataset", target === "tab-uci" ? "uci" : "home");
  window.history.replaceState(null, "", `${url.pathname}${url.search}${url.hash}`);
}
function activateDataset(button, persist = true) {
  const tabs = document.querySelectorAll(".dataset-tab");
  const target = button.dataset.tab || button.getAttribute("aria-controls");
  tabs.forEach(item => { const active = item === button; item.classList.toggle("is-active", active); item.setAttribute("aria-selected", String(active)); });
  document.querySelectorAll(".dataset-tab-panel").forEach(panel => { panel.hidden = panel.id !== target; });
  if (persist) persistDataset(target);
  if (target === "tab-uci") { loadUciReference(); resizeCharts("#tab-uci"); }
}
function setupDatasetTabs() {
  const tabs = document.querySelectorAll(".dataset-tab");
  tabs.forEach(button => button.addEventListener("click", () => activateDataset(button)));
  const requestedDataset = new URLSearchParams(window.location.search).get("dataset");
  const initialTarget = requestedDataset === "uci" || window.location.hash === "#tab-uci" ? "tab-uci" : "tab-home";
  const initialButton = document.querySelector(`[aria-controls="${initialTarget}"]`);
  if (initialButton) activateDataset(initialButton, false);
}
function readModelLabSession() {
  try {
    const value = sessionStorage.getItem(MODEL_LAB_SESSION_KEY);
    return value ? JSON.parse(value) : null;
  } catch (_) { return null; }
}
function writeModelLabSession(data) {
  try { sessionStorage.setItem(MODEL_LAB_SESSION_KEY, JSON.stringify(data)); } catch (_) { /* session storage is optional */ }
}
async function loadModelLab() {
  const button = document.querySelector("#run-model-lab");
  const status = document.querySelector("#model-lab-status");
  button.disabled = true;
  button.hidden = true;
  status.className = "lab-status is-loading";
  status.textContent = "Loading the cached academic experiment…";
  try {
    const data = await api("/api/model-lab");
    writeModelLabSession(data);
    renderModelLab(data);
    status.className = "lab-status";
    status.textContent = `Loaded · ${data.folds} folds · materialized offline · test status: ${data.test_status}.`;
  } catch (error) {
    status.className = "lab-status is-error";
    status.textContent = `Could not load the academic experiment: ${error.message}`;
    button.hidden = false;
    button.disabled = false;
  }
}
function setupModelLab() {
  document.querySelector("#run-model-lab").addEventListener("click", loadModelLab);
  const cached = readModelLabSession();
  if (cached && cached.test_status === "unopened") {
    renderModelLab(cached);
    document.querySelector("#model-lab-status").className = "lab-status";
    document.querySelector("#model-lab-status").textContent = `Loaded from this browser session · ${cached.folds} folds · test status: ${cached.test_status}.`;
    return;
  }
  loadModelLab();
}

function renderRoc(data) {
  const traces = data.curves.map(curve => ({x:curve.points.map(p=>p.fpr), y:curve.points.map(p=>p.tpr), customdata:curve.points.map(p=>p.threshold), mode:"lines+markers", marker:{size:4}, name:curve.model==="lightgbm"?"LightGBM":"Logistic Regression", hovertemplate:"Threshold: %{customdata:.2f}<br>False alarms: %{x:.1%}<br>Cases found: %{y:.1%}<extra></extra>"}));
  const annotations = [{x:.78,y:.76,text:"Random: 50/50",showarrow:false,font:{color:"#64748b"}}];
  data.curves.forEach((curve,index) => annotations.push({x:curve.knee.fpr,y:curve.knee.tpr,text:index===0?"A":"B",showarrow:true,arrowhead:2,ax:index===0?55:-55,ay:index===0?-70:70,bgcolor:"#ffffff",bordercolor:"#2563eb",borderwidth:1,font:{color:"#2563eb",size:14}}));
  Plotly.newPlot("roc-chart", traces, {height:390,margin:{l:70,r:25,t:18,b:96},hovermode:"closest",legend:{orientation:"h",x:.5,y:-.24,xanchor:"center",yanchor:"top"},xaxis:{title:"Allowed false alarms",range:[0,1],tickformat:".0%"},yaxis:{title:"Risk cases found",range:[0,1],tickformat:".0%"},shapes:[{type:"line",x0:0,y0:0,x1:1,y1:1,line:{color:"#94a3b8",dash:"dot"}}],annotations}, plotConfig);
  document.querySelector("#roc-annotations").innerHTML=data.curves.map((curve,index)=>`<article><b>${index===0?"A":"B"} · ${curve.model==="lightgbm"?"LightGBM":"Logistic Regression"}</b><span>Approximate knee: beyond this point, each extra default found costs more false alarms. Threshold ${curve.knee.threshold?.toFixed(2) ?? "—"}.</span></article>`).join("");
}

function renderProbabilities(data) {
  const colors = chartColors;
  const labels = {logistic_regression:"Logistic Regression", lightgbm:"LightGBM"};
  const traces = data.distributions.map(distribution => ({type:"bar", x:distribution.bins.map(bin=>Number(bin)+.025), y:distribution.counts, width:.047, name:labels[distribution.model]||distribution.model, opacity:.58, marker:{color:colors[distribution.model]||"#64748b"}, hovertemplate:`${labels[distribution.model]||distribution.model}<br>Probability range: %{x:.0%}<br>Cases: %{y}<extra></extra>`}));
  const annotations = [{x:.5,y:.98,xref:"x",yref:"paper",text:"Academic line · 0.50",showarrow:false,xanchor:"center",yanchor:"top",bgcolor:"rgba(255,255,255,.86)",bordercolor:"rgba(100,116,139,.45)",borderwidth:1,font:{size:11,color:"#475569"}}];
  Plotly.newPlot("probability-chart-comparison", traces, {height:360,margin:{l:65,r:18,t:32,b:92},barmode:"overlay",hovermode:"x unified",xaxis:{title:"Estimated probability",range:[0,1],tickformat:".0%"},yaxis:{title:"Number of cases"},legend:{orientation:"h",x:.5,y:-.25,xanchor:"center",yanchor:"top"},shapes:[{type:"line",x0:.5,x1:.5,y0:0,y1:1,yref:"paper",line:{dash:"dash",color:"#64748b",width:1.5},opacity:.72},{type:"rect",x0:0,x1:.3,y0:0,y1:1,yref:"paper",fillcolor:"#dbeafe",opacity:.16,line:{width:0}},{type:"rect",x0:.7,x1:1,y0:0,y1:1,yref:"paper",fillcolor:"#fee2e2",opacity:.16,line:{width:0}}],annotations}, plotConfig);
}

function renderCalibration(data) {
  const traces = data.models.map(row => ({
    x: row.points.map(point => point.mean_predicted_probability),
    y: row.points.map(point => point.observed_default_rate),
    mode: "lines+markers",
    name: modelLabel(row.model),
    customdata: row.points.map(point => point.cases),
    hovertemplate: "Predicted: %{x:.1%}<br>Observed: %{y:.1%}<br>Cases: %{customdata}<extra></extra>"
  }));
  traces.push({
    x: [0, 1], y: [0, 1], mode: "lines", name: "Perfect calibration",
    line: {dash: "dash", color: "#94a3b8"}, hoverinfo: "skip"
  });
  Plotly.newPlot("calibration-chart", traces, {
    height: 380,
    margin: {l:65, r:18, t:16, b:75},
    xaxis: {title: "Mean predicted probability", range: [0, 1], tickformat: ".0%"},
    yaxis: {title: "Observed default rate", range: [0, 1], tickformat: ".0%"},
    legend: {orientation: "h", x: 0, y: -.25, xanchor: "left", yanchor: "top"}
  }, plotConfig);
}

function sceneFor(row) { const threshold=Number(row.threshold); if(threshold<=.3) return ["Capture more cases","We lower the line: we find more risk cases, but accept more false alarms."]; if(threshold>=.7) return ["Be more selective","We raise the line: alerts become more precise, but we may leave risk cases out."]; return ["Seek balance","We choose a middle point. F1 summarizes the trade-off between coverage and alert accuracy."]; }
function selectedRow(model) { const value=Number(document.querySelector("#threshold-slider").value); return state.sweeps[model].points.reduce((best,row)=>Math.abs(Number(row.threshold)-value)<Math.abs(Number(best.threshold)-value)?row:best); }
function renderThresholdChart(model,row) { const selected=state.sweeps[model].points; const lines=["precision","recall","f1"].map(metric=>({x:selected.map(r=>r.threshold),y:selected.map(r=>r[metric]),mode:"lines+markers",name:metric==="precision"?"Precision · alert accuracy":metric==="recall"?"Recall · coverage":"F1 · balance",line:{color:chartColors[metric]},marker:{color:chartColors[metric],size:6},hovertemplate:"Threshold: %{x:.2f}<br>Value: %{y:.1%}<extra></extra>"})); Plotly.react(`threshold-chart-${model}`,lines,{height:330,margin:{l:65,r:18,t:12,b:98},legend:{orientation:"h",x:.5,y:-.3,xanchor:"center",yanchor:"top"},xaxis:{title:"Threshold",range:[.1,.9]},yaxis:{title:"Proportion",range:[0,1],tickformat:".0%"},shapes:[{type:"line",x0:row.threshold,x1:row.threshold,y0:0,y1:1,yref:"paper",line:{dash:"dash",color:chartColors.warning}}],annotations:[{x:row.threshold,y:1.05,xref:"x",yref:"paper",text:`Now ${Number(row.threshold).toFixed(2)}`,showarrow:false}]},plotConfig); }
function updateThreshold() { if(!state.sweeps.lightgbm || !state.sweeps.logistic_regression) return; const reference=selectedRow("lightgbm"); const [title,copy]=sceneFor(reference); const threshold=Number(reference.threshold); document.querySelector("#threshold-value").value=threshold.toFixed(2); document.querySelector("#threshold-value").textContent=threshold.toFixed(2); document.querySelector("#threshold-meaning").textContent=`A threshold of ${threshold.toFixed(2)} means: estimated probability ≥ ${(threshold*100).toFixed(0)}% → academic alert. It is not a certainty.`; document.querySelector("#scene-title").textContent=title; document.querySelector("#scene-copy").textContent=copy; document.querySelectorAll(".stop-buttons button").forEach(button=>button.classList.remove("active")); const stop=threshold<=.3?"low":threshold>=.7?"high":"balanced"; document.querySelector(`[data-stop="${stop}"]`).classList.add("active"); document.querySelector("#threshold-model-cards").innerHTML=Object.entries(state.sweeps).map(([model])=>{const row=selectedRow(model);const label=model==="lightgbm"?"LightGBM":"Logistic Regression";return `<article class="model-card"><h3>${label}</h3><div><span>Recall · coverage</span><b>${fmt(row.recall)}</b></div><div><span>Precision · alert accuracy</span><b>${fmt(row.precision)}</b></div><div><span>F1 · balance</span><b>${fmt(row.f1)}</b></div></article>`;}).join(""); Object.entries(state.sweeps).forEach(([model])=>renderThresholdChart(model,selectedRow(model))); }
async function loadSweeps() { const [logistic,lightgbm]=await Promise.all([api("/api/threshold-sweep?model=logistic_regression"),api("/api/threshold-sweep?model=lightgbm")]); state.sweeps={logistic_regression:logistic,lightgbm}; updateThreshold(); }
function setupThreshold() { document.querySelector("#threshold-slider").addEventListener("input",updateThreshold); document.querySelectorAll("[data-stop]").forEach(button=>button.addEventListener("click",()=>{const target=button.dataset.stop==="low"?0.1:button.dataset.stop==="high"?0.9:Number(state.sweeps.lightgbm.best_f1.threshold); document.querySelector("#threshold-slider").value=target; updateThreshold();})); document.querySelector("#play-sweep").addEventListener("click",()=>{if(state.timer) clearInterval(state.timer); let index=0; const points=state.sweeps.lightgbm.points; state.timer=setInterval(()=>{document.querySelector("#threshold-slider").value=points[index].threshold; updateThreshold(); index+=1; if(index>=points.length){clearInterval(state.timer);state.timer=null;}},350);}); loadSweeps(); }
function renderCapacity(data) { document.querySelector("#capacity-value").textContent=`${Math.round(Number(data.capacity)*100)}%`; document.querySelector("#capacity-summary").innerHTML=data.models.map(row=>`<article class="model-card"><h3>${modelLabel(row.model)}</h3><div><span>Cases reviewed</span><b>${row.reviewed_rows}</b></div><div><span>Precision@capacity · alert accuracy</span><b>${fmt(row.precision_at_capacity)}</b></div><div><span>Recall@capacity · coverage</span><b>${fmt(row.recall_at_capacity)}</b></div><div><span>Lift vs prevalence</span><b>${Number(row.lift).toFixed(2)}×</b></div></article>`).join(""); document.querySelector("#capacity-status").textContent=`Validation ranking at ${Math.round(Number(data.capacity)*100)}% review capacity · test remains closed.`; }
async function updateCapacity() { const capacity=Number(document.querySelector("#capacity-slider").value); try { renderCapacity(await api(`/api/policy-capacity?capacity=${capacity.toFixed(2)}`)); } catch(error) { document.querySelector("#capacity-status").textContent=`Could not update policy: ${error.message}`; } }
function setupCapacity() { document.querySelector("#capacity-slider").addEventListener("input",updateCapacity); updateCapacity(); }
function syncFocusValue() { const feature=document.querySelector("#focus-feature"); const value=document.querySelector("#focus-value"); if(feature && value) value.value=state.features[feature.value]??0; }
function applyOverride(key, numeric) {
  state.overrides = {...state.overrides, [key]: numeric};
  state.features = {...state.baseFeatures, ...state.overrides};
  const field = document.querySelector(`#feature-${key}`);
  if (field) field.value = String(numeric);
  document.querySelectorAll(".preset-button").forEach(button => button.classList.remove("active"));
}
function setupQuickEdit() { const feature=document.querySelector("#focus-feature"); const value=document.querySelector("#focus-value"); Object.entries(labels).forEach(([key,label])=>{const option=document.createElement("option"); option.value=key; option.textContent=label; feature.appendChild(option);}); feature.value="PAY_AMT1"; feature.addEventListener("change",syncFocusValue); document.querySelector("#apply-focus").addEventListener("click",()=>{const key=feature.value; const numeric=Number(value.value); if(!Number.isFinite(numeric)) return; if(state.activeExample){applyOverride(key,numeric);}else{state.features[key]=numeric; state.overrides[key]=numeric;} document.querySelector("#preset-status").textContent=`${labels[key]} changed to ${numeric}. You can apply more changes before calculating.`;}); syncFocusValue(); }
function syncFeatureFields() { Object.entries(state.features).forEach(([key,value])=>{const field=document.querySelector(`#feature-${key}`); if(field) field.value=String(value);}); syncFocusValue(); }
function caseOutcome(example) { return example.observed_default_next_month===1 ? "Default recorded next month" : "No default recorded next month"; }
function renderCaseSummary(example) { const summary=document.querySelector("#case-summary"); if(summary) summary.innerHTML=`<b>${example.case_id}</b> · ${example.summary} <span>Recorded result: ${caseOutcome(example)}.</span>`; }
async function setupExamples() { const select=document.querySelector("#example-select"); const summary=document.querySelector("#case-summary"); try { const data=await api("/api/examples"); state.examples=data.cases; select.innerHTML=""; state.examples.forEach(example=>{const option=document.createElement("option"); option.value=example.case_id; option.textContent=`${example.case_id} · ${caseOutcome(example)}`; select.appendChild(option);}); select.addEventListener("change",()=>{const example=state.examples.find(item=>item.case_id===select.value); if(example) renderCaseSummary(example);}); if(state.examples[0]) renderCaseSummary(state.examples[0]); } catch(error) { select.innerHTML=`<option>Cases unavailable</option>`; if(summary) summary.textContent=`Could not load public validation cases: ${error.message}`; return; } document.querySelector("#load-example").addEventListener("click",()=>{const example=state.examples.find(item=>item.case_id===select.value); if(!example) return; state.baseFeatures={...example.features}; state.features={...example.features}; state.overrides={}; state.activeExample=example; renderCaseSummary(example); syncFeatureFields(); document.querySelector("#focus-feature").value="PAY_AMT1"; syncFocusValue(); document.querySelector("#preset-status").textContent=`${example.case_id} loaded. Change any number of variables, then calculate the resulting scenario.`; document.querySelector("#prediction-form button[type=submit]").textContent="Calculate scenario"; document.querySelectorAll(".preset-button").forEach(button=>button.classList.remove("active"));}); }
function setPreset(name) { const values={...defaults}; Object.keys(labels).forEach(key=>{if(categorical.has(key)) values[key]=name==="on-time"?-1:name==="late"?2:0; else values[key]=defaults[key]??2000;}); if(name==="on-time") Object.keys(labels).filter(key=>key.startsWith("PAY_AMT")).forEach(key=>values[key]=5000); if(name==="late") Object.keys(labels).filter(key=>key.startsWith("PAY_AMT")).forEach(key=>values[key]=500); state.baseFeatures={...values}; state.features={...values}; state.overrides={}; state.activeExample=null; syncFeatureFields(); const text=name==="on-time"?"On-time payments: stable history applied.":name==="late"?"Recent delays: higher academic risk signal applied.":"Typical profile: moderate values applied."; document.querySelector("#preset-status").textContent=text; document.querySelectorAll(".preset-button").forEach(button=>button.classList.toggle("active",button.dataset.preset===name)); }
function renderPredictionResult(result) { const observed=state.activeExample?`<p class="observed-result">Recorded result: <b>${caseOutcome(state.activeExample)}</b>.</p>`:""; const changes=result.probability_changes||result.predictions.map(row=>({model:row.model,baseline_probability:row.probability,scenario_probability:row.probability,absolute_change:0,relative_change_pct:0})); const overrides=Object.entries(result.overrides||{}); const changeLabel=overrides.length?`<b>${overrides.length} variable${overrides.length===1?"":"s"}</b> changed: ${overrides.map(([key,value])=>`${labels[key]} = ${value}`).join(" · ")}`:"No overrides; current scenario"; document.querySelector("#prediction-result").hidden=false; document.querySelector("#prediction-result").innerHTML=`<div class="result-intro"><b>What it means:</b> this is the estimated probability that a default will be recorded next month. It is not a certainty or a decision.${observed}<p><b>Scenario:</b> ${changeLabel}. Any value not listed here was preserved from the selected case.</p></div>${changes.map(row=>{const delta=Number(row.absolute_change); const sign=delta>=0?"+":""; const relative=row.relative_change_pct===null?"—":`${row.relative_change_pct>=0?"+":""}${Number(row.relative_change_pct).toFixed(1)}%`; return `<article><h3>${modelLabel(row.model)}</h3><div class="prediction-comparison"><div><span>Baseline</span><strong>${fmt(row.baseline_probability)}</strong></div><div><span>After changes</span><strong>${fmt(row.scenario_probability)}</strong></div><div><span>Change</span><strong class="${delta>0?"change-up":delta<0?"change-down":"change-flat"}">${sign}${(delta*100).toFixed(1)} pp</strong><small>${relative} relative</small></div></div><p>Estimated probability of a default recorded next month.</p></article>`;}).join("")}`; }
function buildForm() { const grid=document.querySelector("#feature-grid"); Object.entries(labels).forEach(([key,label])=>{const wrapper=document.createElement("label"); wrapper.textContent=label; let field; if(categorical.has(key)){field=document.createElement("select"); paymentStatuses.forEach(([value,text])=>{const option=document.createElement("option");option.value=value;option.textContent=`${value}: ${text}`;field.appendChild(option);}); field.value="0";}else{field=document.createElement("input");field.type="number";field.step="any";field.value=defaults[key]??2000;} field.name=key; field.id=`feature-${key}`; field.addEventListener("input",()=>{const numeric=Number(field.value); if(state.activeExample){applyOverride(key,numeric);}else{state.features[key]=numeric; state.overrides[key]=numeric;} if(document.querySelector("#focus-feature").value===key) syncFocusValue(); document.querySelector("#preset-status").textContent=`${label} changed. You can edit more fields before calculating.`;}); wrapper.appendChild(field); grid.appendChild(wrapper);}); document.querySelectorAll(".preset-button").forEach(button=>button.addEventListener("click",()=>setPreset(button.dataset.preset))); setPreset("typical"); setupQuickEdit(); document.querySelector("#prediction-form").addEventListener("submit",async event=>{event.preventDefault(); const payload=state.activeExample?{case_id:state.activeExample.case_id,overrides:state.overrides}:{features:state.features}; const result=await api("/api/predict",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)}); renderPredictionResult(result);}); }
function init() { document.addEventListener("cop-language-change",()=>{if(state.homeAcademic) renderHomeAcademic(state.homeAcademic);}); setupDatasetTabs(); setupHomeViewTabs(); setupHomeStoryMotion(); loadHomeCredit(); window.addEventListener("load",()=>{resizeCharts("#tab-uci");}); }
init();
