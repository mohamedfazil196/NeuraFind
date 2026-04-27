"use strict";

// ─── State ───────────────────────────────────────────────────────────────────
const state = {
  device: null, budget: 25000, priorities: new Set(),
  results: [], chatHistory: [], insightLoaded: false, radarCharts: {},
};

// ─── Device Configurations ───────────────────────────────────────────────────
const CONFIG = {
  mobile: {
    minBudget: 5000, maxBudget: 200000, step: 1000, defBudget: 25000,
    presets: [15000, 25000, 50000, 80000, 100000, 150000],
    priorities: [
      { id: "camera", icon: "📸", name: "Best Camera", desc: "Top-tier photos & videos" },
      { id: "battery", icon: "🔋", name: "Long Battery", desc: "For heavy daily usage" },
      { id: "performance", icon: "🚀", name: "Performance", desc: "Fast multitasking & apps" },
      { id: "gaming", icon: "🎮", name: "Gaming", desc: "High frame rates & cooling" },
      { id: "selfie", icon: "🤳", name: "Great Selfies", desc: "Crisp front camera" },
      { id: "value", icon: "💎", name: "Value for Money", desc: "Best specs per rupee" },
      { id: "5g", icon: "⚡", name: "5G Ready", desc: "Future-proof connectivity" },
    ],
    brands: ["Xiaomi","Samsung","OnePlus","Apple","Realme","Nothing","Google","Motorola","iQOO","Vivo","POCO","Oppo"]
  },
  laptop: {
    minBudget: 30000, maxBudget: 350000, step: 5000, defBudget: 60000,
    presets: [40000, 60000, 80000, 120000, 200000],
    priorities: [
      { id: "performance", icon: "⚡", name: "Raw Performance", desc: "Heavy apps & multitasking" },
      { id: "gaming", icon: "🎮", name: "Gaming", desc: "Dedicated GPU & cooling" },
      { id: "battery", icon: "🔋", name: "All-day Battery", desc: "Work without the charger" },
      { id: "portability", icon: "🪶", name: "Portability", desc: "Lightweight & thin" },
      { id: "display", icon: "🖥️", name: "Display Quality", desc: "Color accurate & sharp" },
      { id: "programming", icon: "👨‍💻", name: "Programming", desc: "More RAM & Storage" },
      { id: "value", icon: "💎", name: "Value for Money", desc: "Best overall balance" },
    ],
    brands: ["Apple","Dell","ASUS","Lenovo","HP","MSI","Acer","Samsung"]
  },
  smartwatch: {
    minBudget: 2000, maxBudget: 90000, step: 1000, defBudget: 10000,
    presets: [3000, 5000, 10000, 25000, 40000],
    priorities: [
      { id: "health", icon: "❤️", name: "Health Tracking", desc: "ECG, SpO2 & Heart Rate" },
      { id: "battery", icon: "🔋", name: "Long Battery", desc: "Multi-day endurance" },
      { id: "fitness", icon: "🏃", name: "Fitness & Sports", desc: "Accurate workout data" },
      { id: "design", icon: "✨", name: "Design & Display", desc: "Premium build quality" },
      { id: "sleep", icon: "😴", name: "Sleep Tracking", desc: "Detailed sleep stages" },
      { id: "waterproof", icon: "🏊", name: "Waterproof", desc: "For swimming & diving" },
    ],
    brands: ["Apple","Samsung","Garmin","Fitbit","Amazfit","Google","Polar","Noise","boAt"]
  }
};
const DEVICE_ICONS = { mobile: "📱", laptop: "💻", smartwatch: "⌚" };

// ─── Particles ───────────────────────────────────────────────────────────────
(function initParticles() {
  const canvas = document.getElementById("particle-canvas");
  const ctx = canvas.getContext("2d");
  let W, H, particles;
  function resize() { W = canvas.width = window.innerWidth; H = canvas.height = window.innerHeight; }
  function mkP() { return { x: Math.random()*W, y: Math.random()*H, r: Math.random()*1.5+0.3, vx: (Math.random()-0.5)*0.2, vy: (Math.random()-0.5)*0.2, color: ["#6c63ff","#a78bfa","#38bdf8","#00f5c4"][Math.floor(Math.random()*4)] }; }
  function init() { resize(); particles = Array.from({length:70}, mkP); }
  function draw() {
    ctx.clearRect(0,0,W,H);
    particles.forEach(p => {
      p.x += p.vx; p.y += p.vy;
      if(p.x<0)p.x=W; if(p.x>W)p.x=0; if(p.y<0)p.y=H; if(p.y>H)p.y=0;
      ctx.beginPath(); ctx.arc(p.x,p.y,p.r,0,Math.PI*2); ctx.fillStyle=p.color; ctx.globalAlpha=0.5; ctx.fill();
    });
    ctx.globalAlpha=1; requestAnimationFrame(draw);
  }
  window.addEventListener("resize", resize); init(); draw();
})();

// ─── Navigation & Wizard ─────────────────────────────────────────────────────
function showSection(name) {
  ["home","history"].forEach(s => document.getElementById(`section-${s}`).classList.toggle("hidden", s !== name));
  document.querySelectorAll(".nav-pill").forEach(n => n.classList.toggle("active", n.textContent.toLowerCase().includes(name)));
  if (name === "history") loadHistory();
}
function goToStep(n) {
  for (let i=1;i<=4;i++) {
    document.getElementById(`step-${i}`).classList.toggle("hidden", i!==n);
    const si = document.getElementById(`si-${i}`);
    si.classList.toggle("active", i===n); si.classList.toggle("done", i<n);
  }
  for (let i=1;i<=3;i++) document.getElementById(`sl-${i}`)?.classList.toggle("done", i<n);
}

// ─── Step 1 ──────────────────────────────────────────────────────────────────
function selectDevice(device) {
  state.device = device;
  document.querySelectorAll(".device-card").forEach(c => c.classList.remove("selected"));
  document.getElementById(`dc-${device}`).classList.add("selected");
  setTimeout(() => { setupBudgetStep(); setupPriorityStep(); goToStep(2); }, 200);
}

// ─── Step 2: Budget ──────────────────────────────────────────────────────────
function setupBudgetStep() {
  const conf = CONFIG[state.device], slider = document.getElementById("budget-slider");
  slider.min = conf.minBudget; slider.max = conf.maxBudget; slider.step = conf.step;
  slider.value = state.budget = conf.defBudget;
  document.getElementById("budget-presets").innerHTML = conf.presets.map(p =>
    `<button class="preset-chip" onclick="setPresetBudget(${p}, this)">₹${p>=100000?(p/100000)+'L':(p/1000)+'K'}</button>`
  ).join("");
  updateBudgetDisplay();
}
function updateBudget() { state.budget = parseFloat(document.getElementById("budget-slider").value); updateBudgetDisplay(); document.querySelectorAll(".preset-chip").forEach(c=>c.classList.remove("active")); }
function setPresetBudget(val, btn) { state.budget=val; document.getElementById("budget-slider").value=val; updateBudgetDisplay(); document.querySelectorAll(".preset-chip").forEach(c=>c.classList.remove("active")); btn.classList.add("active"); }
function updateBudgetDisplay() { document.getElementById("budget-display").textContent = `₹ ${state.budget.toLocaleString("en-IN")}`; }

// ─── Step 3: Priorities ──────────────────────────────────────────────────────
function setupPriorityStep() {
  state.priorities.clear(); state.insightLoaded = false;
  document.getElementById("insight-panel").classList.add("hidden");
  const conf = CONFIG[state.device];
  document.getElementById("priority-grid").innerHTML = conf.priorities.map(p => `
    <div class="priority-chip" id="pri-${p.id}" onclick="togglePriority('${p.id}')">
      <div class="p-check">✓</div><div class="p-icon">${p.icon}</div>
      <div class="p-name">${p.name}</div><div class="p-desc">${p.desc}</div>
    </div>`).join("");
  document.getElementById("brand-select").innerHTML = `<option value="">Any brand</option>` +
    conf.brands.map(b => `<option value="${b}">${b}</option>`).join("");
}
function togglePriority(id) {
  const el = document.getElementById(`pri-${id}`);
  if (state.priorities.has(id)) { state.priorities.delete(id); el.classList.remove("selected"); }
  else { state.priorities.add(id); el.classList.add("selected"); }
}

// ─── Step 4: Run Recommendation ──────────────────────────────────────────────
async function runRecommend() {
  goToStep(4);
  document.getElementById("results-list").innerHTML = "";
  document.getElementById("results-loader").classList.remove("hidden");
  document.getElementById("results-badge").classList.add("hidden");
  document.getElementById("ai-insights-row").classList.add("hidden");
  document.getElementById("ai-insights-row").innerHTML = "";
  document.getElementById("submit-btn").style.pointerEvents = "none";

  const payload = {
    device_type: state.device, budget: state.budget,
    priorities: Array.from(state.priorities),
    brand: document.getElementById("brand-select").value,
    usage: document.getElementById("usage-select").value,
    gaming: document.getElementById("gaming-select").value,
    travel: document.getElementById("travel-select").value,
    camera_priority: document.getElementById("camera-select").value,
  };

  try {
    const res = await fetch("/recommend", { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(payload) });
    const data = await res.json();
    document.getElementById("results-loader").classList.add("hidden");
    document.getElementById("submit-btn").style.pointerEvents = "auto";

    if (data.error) { document.getElementById("results-list").innerHTML = `<div class="empty-state">❌ Error: ${data.error}</div>`; return; }

    state.results = data.recommendations;
    // Source badge
    const srcBadge = document.getElementById("source-badge");
    srcBadge.textContent = data.source === "realtime" ? "🔴 LIVE · Real-Time" : "📊 Dataset";
    srcBadge.className = "source-badge " + (data.source === "realtime" ? "live" : "dataset");

    document.getElementById("results-badge").textContent = `${data.recommendations.length} Top Picks`;
    document.getElementById("results-badge").classList.remove("hidden");
    document.getElementById("btn-compare").style.display = data.recommendations.length > 1 ? "inline-block" : "none";

    // Render AI Insight cards (Personality + Tradeoff)
    renderAIInsights(data.personality, data.tradeoff);
    // Render device cards
    renderResults(data.recommendations);
  } catch (err) {
    document.getElementById("results-loader").classList.add("hidden");
    document.getElementById("results-list").innerHTML = `<div class="empty-state">❌ Network error: ${err.message}</div>`;
    document.getElementById("submit-btn").style.pointerEvents = "auto";
  }
}

// ─── Render AI Insights (Personality + Tradeoff) ─────────────────────────────
function renderAIInsights(personality, tradeoff) {
  const row = document.getElementById("ai-insights-row");
  if ((!personality || !personality.type) && (!tradeoff || !tradeoff.advice)) { row.classList.add("hidden"); return; }
  let html = "";
  if (personality && personality.type) {
    html += `<div class="insight-card personality-card">
      <div class="insight-card-icon">${personality.type.split(" ").pop() || "😌"}</div>
      <div class="insight-card-content">
        <div class="insight-card-label">YOUR AI PERSONALITY</div>
        <div class="insight-card-title">${personality.type}</div>
        <p class="insight-card-text">${personality.explanation || ""}</p>
      </div></div>`;
  }
  if (tradeoff && tradeoff.advice) {
    const icon = tradeoff.should_upgrade ? "💡" : "✅";
    const cls = tradeoff.should_upgrade ? "upgrade" : "optimal";
    html += `<div class="insight-card tradeoff-card ${cls}">
      <div class="insight-card-icon">${icon}</div>
      <div class="insight-card-content">
        <div class="insight-card-label">BUDGET TRADEOFF ANALYSIS</div>
        <div class="insight-card-title">${tradeoff.should_upgrade ? `Spend ₹${(tradeoff.extra_amount||3000).toLocaleString("en-IN")} more?` : "Your budget is optimal!"}</div>
        <p class="insight-card-text">${tradeoff.advice}</p>
        ${tradeoff.improvement ? `<div class="tradeoff-improve">📈 ${tradeoff.improvement}</div>` : ""}
      </div></div>`;
  }
  row.innerHTML = html;
  row.classList.remove("hidden");
}

// ─── Render Results ──────────────────────────────────────────────────────────
function renderResults(recs) {
  const list = document.getElementById("results-list"); list.innerHTML = "";
  Object.values(state.radarCharts).forEach(c => c.destroy()); state.radarCharts = {};
  const ranks = [
    { label: "🥇 First Choice", class: "rank-1" },
    { label: "🥈 Excellent Match", class: "rank-2" },
    { label: "🥉 Great Value", class: "rank-3" }
  ];

  recs.forEach((rec, i) => {
    const r = ranks[i] || { label: `Pick #${i+1}`, class: "rank-4" };
    const specsHtml = Object.entries(rec.specs).map(([k,v]) => `<div class="spec-item"><div class="spec-key">${k}</div><div class="spec-val">${v}</div></div>`).join("");
    const geminiHtml = rec.gemini_explanation ? `<div class="gemini-box"><div class="gemini-box-hdr">⚡ AI Insight</div><p>${rec.gemini_explanation}</p></div>` : "";
    const chartId = `radar-${i}`;
    const liveBadge = rec.is_live_gemini ? `<span class="live-badge">🔴 LIVE AI PICK</span>` : "";
    const amazonUrl = `https://www.amazon.in/s?k=${encodeURIComponent(rec.name)}`;
    const flipkartUrl = `https://www.flipkart.com/search?q=${encodeURIComponent(rec.name)}`;

    const card = document.createElement("div");
    card.className = "result-card"; card.style.animationDelay = `${i*0.15}s`;
    card.innerHTML = `
      <div class="card-rank-strip">
        <div class="rank-badge"><span class="rank-emoji">${r.label.split(" ")[0]}</span><span class="rank-label">${r.label.split(" ").slice(1).join(" ")} ${liveBadge}</span></div>
        <div class="card-score-pills">
          <div class="score-pill"><span class="score-num">${rec.score}%</span><span class="score-lbl">Match</span></div>
          <div class="score-pill conf"><span class="score-num">${rec.confidence}%</span><span class="score-lbl">AI Conf.</span></div>
        </div>
      </div>
      <div class="card-body">
        <div class="card-left">
          <div class="card-name">${rec.name}</div>
          <div class="card-brand">Brand: ${rec.brand}</div>
          <div class="match-bar-wrap"><div class="match-bar-label"><span>Overall AI Compatibility</span><span>${rec.score}%</span></div><div class="match-bar-bg"><div class="match-bar-fill" id="bar-${i}" style="width:0%"></div></div></div>
          <div class="specs-grid">${specsHtml}</div>
          <div class="card-reason">${rec.reason}</div>
          ${geminiHtml}
        </div>
        <div class="card-right"><div class="radar-wrap"><canvas id="${chartId}"></canvas></div><div class="radar-title">Spec Balance</div></div>
      </div>
      <div class="card-footer">
        <div class="buy-buttons">
          <a href="${amazonUrl}" target="_blank" class="buy-btn amazon-btn">🛒 Buy on Amazon</a>
          <a href="${flipkartUrl}" target="_blank" class="buy-btn flipkart-btn">🛍️ Buy on Flipkart</a>
        </div>
      </div>`;
    list.appendChild(card);
    setTimeout(() => { document.getElementById(`bar-${i}`).style.width = `${rec.score}%`; }, 100+i*150);
    setTimeout(() => drawRadar(chartId, rec.radar, i), 200+i*100);
  });
}

function drawRadar(id, data, idx) {
  const ctx = document.getElementById(id);
  if (!ctx || !data) return;
  const colors = [["rgba(108,99,255,0.7)","rgba(108,99,255,0.2)"],["rgba(56,189,248,0.7)","rgba(56,189,248,0.2)"],["rgba(167,139,250,0.7)","rgba(167,139,250,0.2)"]][idx%3];
  state.radarCharts[id] = new Chart(ctx, {
    type:"radar",
    data:{ labels:data.labels, datasets:[{ data:data.values, borderColor:colors[0], backgroundColor:colors[1], borderWidth:1.5, pointBackgroundColor:colors[0], pointBorderColor:"transparent", pointRadius:2 }] },
    options:{ animation:{duration:1000,easing:"easeOutQuart"}, responsive:true, maintainAspectRatio:true, plugins:{legend:{display:false}}, scales:{r:{min:0,max:100, angleLines:{color:"rgba(255,255,255,0.06)"}, grid:{color:"rgba(255,255,255,0.04)"}, ticks:{display:false}, pointLabels:{color:"#9aabcf",font:{size:8.5,family:"Inter"}}}} }
  });
}

// ─── Market Insight ──────────────────────────────────────────────────────────
async function loadMarketInsight() {
  if (state.insightLoaded) { document.getElementById("insight-panel").classList.toggle("hidden"); return; }
  const panel=document.getElementById("insight-panel"), loader=document.getElementById("insight-loader"), content=document.getElementById("insight-content");
  panel.classList.remove("hidden"); loader.style.display="block"; content.innerHTML="";
  try {
    const res = await fetch("/market-insight", { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({category:state.device,budget:state.budget}) });
    const data = await res.json(); loader.style.display="none";
    content.innerHTML = `<div class="insight-summary">${data.summary||""}</div>
      <div style="margin-bottom:12px"><div class="insight-label">🔥 Trending Now</div><div class="insight-chips">${(data.hot_picks||[]).map(p=>`<span class="insight-chip">${p}</span>`).join("")}</div></div>
      <div class="insight-warning">⚠️ ${data.avoid||""}</div><div class="insight-protip">💡 Pro Tip: ${data.pro_tip||""}</div>`;
    state.insightLoaded = true;
  } catch(e) { loader.style.display="none"; content.innerHTML=`<div style="color:var(--accent-r)">Error loading insight.</div>`; }
}

// ─── Export PDF ──────────────────────────────────────────────────────────────
function exportPDF() {
  if (!state.results.length) { alert("No results to export."); return; }
  const { jsPDF } = window.jspdf; const doc = new jsPDF({unit:"mm",format:"a4"}); let y=20;
  doc.setFillColor(6,9,19); doc.rect(0,0,210,297,"F");
  doc.setFont("helvetica","bold"); doc.setTextColor(108,99,255); doc.setFontSize(22);
  doc.text("NeuraFind — AI Device Match (Live)",20,y); y+=10;
  doc.setFont("helvetica","normal"); doc.setFontSize(11); doc.setTextColor(154,171,207);
  doc.text(`Category: ${state.device} | Budget: Rs. ${state.budget.toLocaleString("en-IN")}`,20,y); y+=15;
  state.results.forEach((rec,i) => {
    if(y>250){doc.addPage();doc.setFillColor(6,9,19);doc.rect(0,0,210,297,"F");y=20;}
    doc.setFont("helvetica","bold"); doc.setFontSize(14); doc.setTextColor(240,244,255);
    doc.text(`#${i+1} - ${rec.name} (${rec.brand})`,20,y); y+=7;
    doc.setFont("helvetica","normal"); doc.setFontSize(10); doc.setTextColor(108,99,255);
    doc.text(`Match: ${rec.score}% | AI Confidence: ${rec.confidence}%`,24,y); y+=6;
    doc.setTextColor(154,171,207);
    Object.entries(rec.specs).forEach(([k,v])=>{doc.text(`• ${k}: ${v}`,24,y);y+=5;});
    if(rec.gemini_explanation){doc.setFont("helvetica","italic");doc.setTextColor(167,139,250);const lines=doc.splitTextToSize(`AI: ${rec.gemini_explanation}`,160);lines.forEach(l=>{doc.text(l,24,y);y+=5;});doc.setFont("helvetica","normal");}
    y+=8;
  });
  doc.save(`neurafind-${state.device}-${Date.now()}.pdf`);
}

// ─── History ─────────────────────────────────────────────────────────────────
async function loadHistory() {
  try {
    const res = await fetch("/history"); const data = await res.json();
    const c = document.getElementById("history-list"); if(!data.history?.length) return;
    c.innerHTML = data.history.map((h,i) => `<div class="history-card" style="animation-delay:${i*0.1}s"><div class="history-icon">${DEVICE_ICONS[h.device_type]||"⚡"}</div><div class="history-info"><div class="history-name">Top: ${h.top_result}</div><div class="history-meta">₹${parseInt(h.budget).toLocaleString("en-IN")} · ${h.priorities.join(", ")||"No priorities"}</div></div><div class="history-score">${h.score}%</div></div>`).join("");
  } catch(e){}
}

// ─── Chat ────────────────────────────────────────────────────────────────────
function toggleChat() { const p=document.getElementById("chat-panel"); p.classList.toggle("hidden"); if(!p.classList.contains("hidden"))document.getElementById("chat-input").focus(); }
function handleChatKey(e) { if(e.key==="Enter")sendChat(); }
async function sendChat() {
  const input=document.getElementById("chat-input"), msg=input.value.trim(); if(!msg) return;
  input.value=""; appendChat("user",msg); appendTyping();
  const history = state.chatHistory.map(m=>({role:m.role==="user"?"user":"model",parts:[{text:m.text}]}));
  state.chatHistory.push({role:"user",text:msg});
  try {
    const res = await fetch("/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:msg,history})});
    const data = await res.json(); removeTyping();
    const reply = data.reply||data.error||"Error."; state.chatHistory.push({role:"model",text:reply}); appendChat("bot",reply);
  } catch(e) { removeTyping(); appendChat("bot","Network error."); }
}
function appendChat(role,text) { const c=document.getElementById("chat-messages"),d=document.createElement("div"); d.className=`chat-msg ${role}`; d.innerHTML=`<div class="msg-bubble">${text.replace(/\n/g,"<br>")}</div>`; c.appendChild(d); c.scrollTop=c.scrollHeight; }
function appendTyping() { const c=document.getElementById("chat-messages"),d=document.createElement("div"); d.id="chat-typing"; d.className="chat-msg bot chat-typing"; d.innerHTML=`<div class="msg-bubble"><div class="dot-dot"></div><div class="dot-dot"></div><div class="dot-dot"></div></div>`; c.appendChild(d); c.scrollTop=c.scrollHeight; }
function removeTyping() { document.getElementById("chat-typing")?.remove(); }

// ─── Battle Mode ─────────────────────────────────────────────────────────────
let battleChartInstance = null;
function openBattleMode() {
  if(state.results.length<2) return;
  const a=state.results[0], b=state.results[1];
  document.getElementById('v-title-1').textContent=a.name; document.getElementById('v-title-2').textContent=b.name;
  const sd=document.getElementById('battle-specs-list'), allKeys=Object.keys(a.specs);
  sd.innerHTML = allKeys.map(key=>`<div class="spec-battle-row"><div class="spec-battle-label">${key}</div><div class="spec-battle-values"><div class="spec-val a">${a.specs[key]||'N/A'}</div><div class="spec-sep"></div><div class="spec-val b">${b.specs[key]||'N/A'}</div></div></div>`).join("");
  const ctx = document.getElementById('battleChart').getContext('2d');
  if(battleChartInstance) battleChartInstance.destroy();
  document.getElementById('battle-modal').classList.remove('hidden');
  battleChartInstance = new Chart(ctx, {
    type:"radar",
    data:{ labels:a.radar.labels, datasets:[
      {label:a.name,data:a.radar.values,borderColor:"rgba(108,99,255,0.8)",backgroundColor:"rgba(108,99,255,0.3)",borderWidth:2,pointBackgroundColor:"rgba(108,99,255,1)"},
      {label:b.name,data:b.radar.values,borderColor:"rgba(0,245,196,0.8)",backgroundColor:"rgba(0,245,196,0.3)",borderWidth:2,pointBackgroundColor:"rgba(0,245,196,1)"}
    ]},
    options:{ animation:{duration:1000,easing:"easeOutQuart"}, responsive:true, maintainAspectRatio:false, plugins:{legend:{display:true,labels:{color:"#f0f4ff",font:{family:"Inter",size:12}}}}, scales:{r:{min:0,max:100,angleLines:{color:"rgba(255,255,255,0.1)"},grid:{color:"rgba(255,255,255,0.06)"},ticks:{display:false},pointLabels:{color:"#9aabcf",font:{size:10,family:"Inter"}}}}}
  });
}
function closeBattleMode() { document.getElementById('battle-modal').classList.add('hidden'); }

goToStep(1);
