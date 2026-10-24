const labels = {
  LIMIT_BAL: "Credit limit", PAY_0: "Payment status · September", PAY_2: "Payment status · August", PAY_3: "Payment status · July", PAY_4: "Payment status · June", PAY_5: "Payment status · May", PAY_6: "Payment status · April",
  BILL_AMT1: "Balance · September", BILL_AMT2: "Balance · August", BILL_AMT3: "Balance · July", BILL_AMT4: "Balance · June", BILL_AMT5: "Balance · May", BILL_AMT6: "Balance · April",
  PAY_AMT1: "Payment made · September", PAY_AMT2: "Payment made · August", PAY_AMT3: "Payment made · July", PAY_AMT4: "Payment made · June", PAY_AMT5: "Payment made · May", PAY_AMT6: "Payment made · April"
};
const paymentStatuses = [[-2,"No consumption"],[-1,"On-time payment"],[0,"No delay"],[1,"1 month late"],[2,"2 months late"],[3,"3 months late"],[4,"4 months late"],[5,"5 months late"],[6,"6 months late"],[7,"7 months late"],[8,"8 months late"],[9,"9+ months late"]];
const defaults = {LIMIT_BAL:50000, BILL_AMT1:20000, BILL_AMT2:20000, BILL_AMT3:20000, BILL_AMT4:20000, BILL_AMT5:20000, BILL_AMT6:20000};
const categorical = new Set(["PAY_0","PAY_2","PAY_3","PAY_4","PAY_5","PAY_6"]);
const state = { sweeps:{}, timer:null, features:{}, baseFeatures:{}, overrides:{}, examples:[], activeExample:null };
const fmt = (value) => `${(Number(value) * 100).toFixed(1)}%`;
const plotConfig = {displayModeBar:false, scrollZoom:false, responsive:true};
const MODEL_LAB_SESSION_KEY = "cop-model-lab-session-v1";
const api = async (path, options={}) => { const response = await fetch(path, options); if (!response.ok) throw new Error(await response.text()); return response.json(); };

function renderMetrics(data) {
  const body = document.querySelector("#metrics-table tbody");
  body.innerHTML = data.validation.map(row => `<tr><td><b>${row.model}</b></td><td>${Number(row.roc_auc).toFixed(3)}</td><td>${fmt(row.average_precision)}</td><td>${fmt(row.recall)}</td><td>${fmt(row.f1)}</td><td>${Number(row.brier_score).toFixed(3)}</td></tr>`).join("");
}

function modelLabel(name) { return name === "lightgbm" ? "LightGBM" : name === "knn" ? "KNN" : "Logistic Regression"; }
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
  const chartRows = Object.entries(data.models).flatMap(([name, payload]) => payload.candidates.map(candidate => ({name, candidate})));
  const apValues = chartRows.map(({candidate}) => candidate.cross_validation.average_precision);
  const bestAp = Math.max(...apValues);
  const minimumAp = Math.min(...apValues);
  const spread = Math.max(bestAp - minimumAp, 0.01);
  Plotly.newPlot("model-lab-chart", [{
    type: "scatter",
    mode: "markers+text",
    orientation: "h",
    y: chartRows.map(({name, candidate}) => trialLabel(name, candidate)),
    x: apValues,
    error_x: {type: "data", array: chartRows.map(({candidate}) => candidate.cross_validation_std.average_precision), visible: true},
    text: chartRows.map(({candidate}) => candidate.selected ? `Selected · #${candidate.rank}` : `#${candidate.rank}`),
    textposition: "middle right",
    marker: {size: chartRows.map(({candidate}) => candidate.selected ? 13 : 9), color: chartRows.map(({name, candidate}) => candidate.selected ? "#2563eb" : name === "knn" ? "#94a3b8" : "#b9c9e8")},
    customdata: chartRows.map(({candidate}) => [parameterText(candidate.parameters), candidate.cross_validation_std.average_precision, candidate.rank]),
    hovertemplate: "%{y}<br>CV AP: %{x:.2%} ± %{customdata[1]:.2%}<br>Rank: %{customdata[2]}<br>%{customdata[0]}<extra></extra>"
  }], {height: Math.max(300, chartRows.length * 34), margin:{l:20,r:90,t:18,b:55}, xaxis:{title:"Average Precision · train CV",tickformat:".1%",range:[Math.max(0, minimumAp - spread * 0.35), Math.min(1, bestAp + spread * 0.35)]}, yaxis:{autorange:"reversed",automargin:true}, showlegend:false}, plotConfig);
  requestAnimationFrame(() => {
    ["#model-lab-chart"].forEach(selector => {
      const chart = document.querySelector(selector);
      if (chart && window.Plotly) Plotly.Plots.resize(chart);
    });
  });
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
  status.textContent = "Running cross-validation on train in the background. This may take a minute…";
  try {
    const data = await api("/api/model-lab");
    writeModelLabSession(data);
    renderModelLab(data);
    status.className = "lab-status";
    status.textContent = `Complete · ${data.folds} folds · cached for this server process · test status: ${data.test_status}.`;
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
  Plotly.newPlot("roc-chart", traces, {height:390,margin:{l:70,r:25,t:18,b:96},hovermode:"closest",legend:{orientation:"h",x:0,y:-0.24,xanchor:"left",yanchor:"top"},xaxis:{title:"Allowed false alarms",range:[0,1],tickformat:".0%"},yaxis:{title:"Risk cases found",range:[0,1],tickformat:".0%"},shapes:[{type:"line",x0:0,y0:0,x1:1,y1:1,line:{color:"#94a3b8",dash:"dot"}}],annotations}, plotConfig);
  document.querySelector("#roc-annotations").innerHTML=data.curves.map((curve,index)=>`<article><b>${index===0?"A":"B"} · ${curve.model==="lightgbm"?"LightGBM":"Logistic Regression"}</b><span>Approximate knee: beyond this point, each extra default found costs more false alarms. Threshold ${curve.knee.threshold?.toFixed(2) ?? "—"}.</span></article>`).join("");
}

function renderProbabilities(data) {
  data.distributions.forEach(distribution => {
    const trace = {type:"bar", x:distribution.bins.map(bin=>Number(bin)+.025), y:distribution.counts, width:.047, name:distribution.model, marker:{color:distribution.model==="lightgbm"?"#2563eb":"#f59e0b"}, hovertemplate:"Probability range: %{x:.0%}<br>Cases: %{y}<extra></extra>"};
    const max=Math.max(...distribution.counts);
    const annotations = [{x:.5,y:1.08,xref:"x",yref:"paper",text:"Academic line 0.50",showarrow:false},{x:distribution.highest_bin/20+.025,y:max,text:"Most cases here",showarrow:true,arrowhead:2,ax:35,ay:-35,bgcolor:"rgba(255,255,255,.9)"}];
    Plotly.newPlot(`probability-chart-${distribution.model}`, [trace], {height:330,margin:{l:65,r:18,t:12,b:58},xaxis:{title:"Estimated probability",range:[0,1],tickformat:".0%"},yaxis:{title:"Number of cases"},shapes:[{type:"line",x0:.5,x1:.5,y0:0,y1:1,yref:"paper",line:{dash:"dash",color:"#64748b"}},{type:"rect",x0:0,x1:.3,y0:0,y1:1,yref:"paper",fillcolor:"#dbeafe",opacity:.22,line:{width:0}},{type:"rect",x0:.7,x1:1,y0:0,y1:1,yref:"paper",fillcolor:"#fee2e2",opacity:.22,line:{width:0}}],annotations}, plotConfig);
  });
}

function sceneFor(row) { const threshold=Number(row.threshold); if(threshold<=.3) return ["Capture more cases","We lower the line: we find more risk cases, but accept more false alarms."]; if(threshold>=.7) return ["Be more selective","We raise the line: alerts become more precise, but we may leave risk cases out."]; return ["Seek balance","We choose a middle point. F1 summarizes the trade-off between coverage and alert accuracy."]; }
function selectedRow(model) { const value=Number(document.querySelector("#threshold-slider").value); return state.sweeps[model].points.reduce((best,row)=>Math.abs(Number(row.threshold)-value)<Math.abs(Number(best.threshold)-value)?row:best); }
function renderThresholdChart(model,row) { const selected=state.sweeps[model].points; const lines=["precision","recall","f1"].map(metric=>({x:selected.map(r=>r.threshold),y:selected.map(r=>r[metric]),mode:"lines+markers",name:metric==="precision"?"Precision · alert accuracy":metric==="recall"?"Recall · coverage":"F1 · balance",hovertemplate:"Threshold: %{x:.2f}<br>Value: %{y:.1%}<extra></extra>"})); Plotly.react(`threshold-chart-${model}`,lines,{height:330,margin:{l:65,r:18,t:12,b:98},legend:{orientation:"h",x:0,y:-0.3,xanchor:"left",yanchor:"top"},xaxis:{title:"Threshold",range:[.1,.9]},yaxis:{title:"Proportion",range:[0,1],tickformat:".0%"},shapes:[{type:"line",x0:row.threshold,x1:row.threshold,y0:0,y1:1,yref:"paper",line:{dash:"dash",color:"#111827"}}],annotations:[{x:row.threshold,y:1.05,xref:"x",yref:"paper",text:`Now ${Number(row.threshold).toFixed(2)}`,showarrow:false}]},plotConfig); }
function updateThreshold() { if(!state.sweeps.lightgbm || !state.sweeps.logistic_regression) return; const reference=selectedRow("lightgbm"); const [title,copy]=sceneFor(reference); const threshold=Number(reference.threshold); document.querySelector("#threshold-value").value=threshold.toFixed(2); document.querySelector("#threshold-value").textContent=threshold.toFixed(2); document.querySelector("#threshold-meaning").textContent=`A threshold of ${threshold.toFixed(2)} means: estimated probability ≥ ${(threshold*100).toFixed(0)}% → academic alert. It is not a certainty.`; document.querySelector("#scene-title").textContent=title; document.querySelector("#scene-copy").textContent=copy; document.querySelectorAll(".stop-buttons button").forEach(button=>button.classList.remove("active")); const stop=threshold<=.3?"low":threshold>=.7?"high":"balanced"; document.querySelector(`[data-stop="${stop}"]`).classList.add("active"); document.querySelector("#threshold-model-cards").innerHTML=Object.entries(state.sweeps).map(([model])=>{const row=selectedRow(model);const label=model==="lightgbm"?"LightGBM":"Logistic Regression";return `<article class="model-card"><h3>${label}</h3><div><span>Recall · coverage</span><b>${fmt(row.recall)}</b></div><div><span>Precision · alert accuracy</span><b>${fmt(row.precision)}</b></div><div><span>F1 · balance</span><b>${fmt(row.f1)}</b></div></article>`;}).join(""); Object.entries(state.sweeps).forEach(([model])=>renderThresholdChart(model,selectedRow(model))); }
async function loadSweeps() { const [logistic,lightgbm]=await Promise.all([api("/api/threshold-sweep?model=logistic_regression"),api("/api/threshold-sweep?model=lightgbm")]); state.sweeps={logistic_regression:logistic,lightgbm}; updateThreshold(); }
function setupThreshold() { document.querySelector("#threshold-slider").addEventListener("input",updateThreshold); document.querySelectorAll("[data-stop]").forEach(button=>button.addEventListener("click",()=>{const target=button.dataset.stop==="low"?0.1:button.dataset.stop==="high"?0.9:Number(state.sweeps.lightgbm.best_f1.threshold); document.querySelector("#threshold-slider").value=target; updateThreshold();})); document.querySelector("#play-sweep").addEventListener("click",()=>{if(state.timer) clearInterval(state.timer); let index=0; const points=state.sweeps.lightgbm.points; state.timer=setInterval(()=>{document.querySelector("#threshold-slider").value=points[index].threshold; updateThreshold(); index+=1; if(index>=points.length){clearInterval(state.timer);state.timer=null;}},350);}); loadSweeps(); }
function syncFocusValue() { const feature=document.querySelector("#focus-feature"); const value=document.querySelector("#focus-value"); if(feature && value) value.value=state.features[feature.value]??0; }
function setupQuickEdit() { const feature=document.querySelector("#focus-feature"); const value=document.querySelector("#focus-value"); Object.entries(labels).forEach(([key,label])=>{const option=document.createElement("option"); option.value=key; option.textContent=label; feature.appendChild(option);}); feature.value="PAY_AMT1"; feature.addEventListener("change",syncFocusValue); document.querySelector("#apply-focus").addEventListener("click",()=>{const key=feature.value; const numeric=Number(value.value); state.features[key]=numeric; state.overrides[key]=numeric; const field=document.querySelector(`#feature-${key}`); if(field) field.value=String(numeric); document.querySelector("#preset-status").textContent=`Change saved: ${labels[key]}. The API will modify only this case field.`; document.querySelectorAll(".preset-button").forEach(button=>button.classList.remove("active"));}); syncFocusValue(); }
function syncFeatureFields() { Object.entries(state.features).forEach(([key,value])=>{const field=document.querySelector(`#feature-${key}`); if(field) field.value=String(value);}); syncFocusValue(); }
async function setupExamples() { const data=await api("/api/examples"); state.examples=data.cases; const select=document.querySelector("#example-select"); state.examples.forEach(example=>{const option=document.createElement("option"); option.value=example.case_id; option.textContent=`${example.case_id} · observed outcome: ${example.observed_default_next_month===1?"default":"no default"}`; select.appendChild(option);}); document.querySelector("#load-example").addEventListener("click",()=>{const example=state.examples.find(item=>item.case_id===select.value); if(!example) return; state.baseFeatures={...example.features}; state.features={...example.features}; state.overrides={}; state.activeExample=example; syncFeatureFields(); document.querySelector("#preset-status").textContent=`${example.case_id} loaded. You can change one variable while keeping the rest of the case.`; document.querySelectorAll(".preset-button").forEach(button=>button.classList.remove("active"));}); }
function setPreset(name) { const values={...defaults}; Object.keys(labels).forEach(key=>{if(categorical.has(key)) values[key]=name==="on-time"?-1:name==="late"?2:0; else values[key]=defaults[key]??2000;}); if(name==="on-time") Object.keys(labels).filter(key=>key.startsWith("PAY_AMT")).forEach(key=>values[key]=5000); if(name==="late") Object.keys(labels).filter(key=>key.startsWith("PAY_AMT")).forEach(key=>values[key]=500); state.baseFeatures={...values}; state.features={...values}; state.overrides={}; state.activeExample=null; syncFeatureFields(); const text=name==="on-time"?"On-time payments: stable history applied.":name==="late"?"Recent delays: higher academic risk signal applied.":"Typical profile: moderate values applied."; document.querySelector("#preset-status").textContent=text; document.querySelectorAll(".preset-button").forEach(button=>button.classList.toggle("active",button.dataset.preset===name)); }
function buildForm() { const grid=document.querySelector("#feature-grid"); Object.entries(labels).forEach(([key,label])=>{const wrapper=document.createElement("label"); wrapper.textContent=label; let field; if(categorical.has(key)){field=document.createElement("select"); paymentStatuses.forEach(([value,text])=>{const option=document.createElement("option");option.value=value;option.textContent=`${value}: ${text}`;field.appendChild(option);}); field.value="0";}else{field=document.createElement("input");field.type="number";field.step="1000";field.value=defaults[key]??2000;} field.name=key; field.id=`feature-${key}`; field.addEventListener("input",()=>{state.features[key]=Number(field.value); state.overrides[key]=Number(field.value); if(document.querySelector("#focus-feature").value===key) syncFocusValue(); document.querySelector("#preset-status").textContent=`Change saved: ${label}. The remaining values stay unchanged.`; document.querySelectorAll(".preset-button").forEach(button=>button.classList.remove("active"));}); wrapper.appendChild(field); grid.appendChild(wrapper);}); document.querySelectorAll(".preset-button").forEach(button=>button.addEventListener("click",()=>setPreset(button.dataset.preset))); setPreset("typical"); setupQuickEdit(); setupExamples(); document.querySelector("#prediction-form").addEventListener("submit",async event=>{event.preventDefault(); const payload=state.activeExample?{case_id:state.activeExample.case_id,overrides:state.overrides}:{features:state.features}; const result=await api("/api/predict",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)}); document.querySelector("#prediction-result").hidden=false; const observed=state.activeExample?`<p class="observed-result">Observed validation outcome: <b>${state.activeExample.observed_default_next_month===1?"default recorded":"no default recorded"}</b>.</p>`:""; document.querySelector("#prediction-result").innerHTML=`<div class="result-intro"><b>What it means:</b> each percentage is the estimated probability that a default will be recorded next month. It is not a certainty or a decision.${observed}</div>${result.predictions.map(row=>`<article><h3>${row.model==="lightgbm"?"LightGBM":"Logistic Regression"}</h3><strong>${fmt(row.probability)}</strong><p>Estimated probability of a default recorded next month</p></article>`).join("")}`;}); }
async function init() { try { const [overview,metrics,roc,probabilities]=await Promise.all([api("/api/overview"),api("/api/metrics"),api("/api/roc"),api("/api/probabilities")]); document.querySelector("#run-id").textContent=`Run ${overview.run_id}`; renderMetrics(metrics); renderRoc(roc); renderProbabilities(probabilities); setupThreshold(); setupModelLab(); buildForm(); } catch(error) { document.body.innerHTML=`<main class="panel"><h1>Could not load the API</h1><p>${error.message}</p><p>Start the backend with <code>uvicorn cop.api:app --reload --port 8000</code>.</p>`; } }
init();
