// SOC Triage Agent UI: alert queue, live trace waterfall, approvals, report.

const state = { alerts: [], selected: null, run: null, tab: "report", spanId: null, poll: null, open: {}, view: "run", playbook: null };
const $ = (sel) => document.querySelector(sel);

// Line icons drawn in the SF Symbols style (24px grid, rounded 1.7 strokes).
const ICONS = {
  shield: '<path d="M12 3l7 3v5.2c0 4.3-2.9 8-7 9.8-4.1-1.8-7-5.5-7-9.8V6z"/><path d="M9 12l2 2 4-4"/>',
  search: '<circle cx="11" cy="11" r="6.5"/><path d="M16 16l4 4"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  trash: '<path d="M5 7h14M10 7V5h4v2M7 7l.8 12.2a1 1 0 0 0 1 .8h6.4a1 1 0 0 0 1-.8L17 7"/>',
  play: '<path d="M8 5.8v12.4a.8.8 0 0 0 1.2.7l10-6.2a.8.8 0 0 0 0-1.4l-10-6.2A.8.8 0 0 0 8 5.8z"/>',
  refresh: '<path d="M19.5 12a7.5 7.5 0 1 1-2.2-5.3"/><path d="M19.5 4.5v4h-4"/>',
  doc: '<path d="M7 3h7l5 5v12a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z"/><path d="M14 3v5h5M9.5 13h6M9.5 16.5h6"/>',
  checkCircle: '<circle cx="12" cy="12" r="8.5"/><path d="M8.5 12.3l2.3 2.3 4.7-4.8"/>',
  timeline: '<path d="M4 6.5h9M8 12h12M6 17.5h7"/>',
  bolt: '<path d="M13 3L5.5 13H11l-1 8 7.5-10H12z"/>',
  tag: '<path d="M3.5 12.2V4.5a1 1 0 0 1 1-1h7.7l8.3 8.3a1 1 0 0 1 0 1.4l-7.3 7.3a1 1 0 0 1-1.4 0z"/><circle cx="8" cy="8" r="1.3"/>',
  gauge: '<path d="M4.2 17a8.5 8.5 0 1 1 15.6 0"/><path d="M12 15l3.5-4.5"/><circle cx="12" cy="15.5" r="1"/>',
  list: '<path d="M9.5 6.5h10M9.5 12h10M9.5 17.5h10"/><circle cx="5" cy="6.5" r=".9"/><circle cx="5" cy="12" r=".9"/><circle cx="5" cy="17.5" r=".9"/>',
  warning: '<path d="M10.3 4.3L2.9 17.6A2 2 0 0 0 4.6 20.6h14.8a2 2 0 0 0 1.7-3L13.7 4.3a2 2 0 0 0-3.4 0z"/><path d="M12 9.5v4M12 17h.01"/>',
  history: '<path d="M3.5 12a8.5 8.5 0 1 0 2.5-6"/><path d="M3.5 4.5V8.5h4"/><path d="M12 8v4.2l3 1.8"/>',
  book: '<path d="M5 5.5A2.5 2.5 0 0 1 7.5 3H19v15H7.5A2.5 2.5 0 0 0 5 20.5z"/><path d="M5 20.5A2.5 2.5 0 0 1 7.5 18H19v3H7.5"/>',
  person: '<circle cx="12" cy="8" r="3.8"/><path d="M4.5 20.5c.6-3.9 3.7-6 7.5-6s6.9 2.1 7.5 6"/>',
  cpu: '<rect x="6.5" y="6.5" width="11" height="11" rx="2"/><path d="M10 3v3.5M14 3v3.5M10 17.5V21M14 17.5V21M3 10h3.5M3 14h3.5M17.5 10H21M17.5 14H21"/>',
  chevron: '<path d="M9 5.5l6.5 6.5L9 18.5"/>',
  chevronDown: '<path d="M5.5 9l6.5 6.5L18.5 9"/>',
  chevronLeft: '<path d="M15 5.5L8.5 12l6.5 6.5"/>',
  pencil: '<path d="M4 20l1-4.5L15.5 5a2.1 2.1 0 0 1 3 3L8 18.5z"/><path d="M13.5 7l3 3"/>',
  eye: '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z"/><circle cx="12" cy="12" r="3"/>',
  save: '<path d="M5 4h11l3 3v12a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1z"/><path d="M8 4v5h7V4M8 20v-6h8v6"/>',
  export: '<path d="M12 14.5V3.5M8 7.5l4-4 4 4"/><path d="M6 11H5v9.5h14V11h-1"/>',
  server: '<rect x="4" y="4" width="16" height="7" rx="2"/><rect x="4" y="13" width="16" height="7" rx="2"/><path d="M8 7.5h.01M8 16.5h.01"/>',
  desktop: '<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M9 20h6M12 16v4"/>',
  clock: '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
  sparkles: '<path d="M12 3.5l1.6 4.9 4.9 1.6-4.9 1.6L12 16.5l-1.6-4.9L5.5 10l4.9-1.6z"/><path d="M18.5 15.5l.7 1.8 1.8.7-1.8.7-.7 1.8-.7-1.8-1.8-.7 1.8-.7z"/>',
  check: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
  xmark: '<path d="M6.5 6.5l11 11M17.5 6.5l-11 11"/>',
  hand: '<path d="M8 13V6.5a1.5 1.5 0 0 1 3 0V11M11 10.5V5a1.5 1.5 0 0 1 3 0v5.5M14 10.5V6.5a1.5 1.5 0 0 1 3 0V14a7 7 0 0 1-7 7h-.5a6 6 0 0 1-4.6-2.2L3.6 15.4a1.5 1.5 0 0 1 2.3-1.9L8 15.5"/>',
  arrowUturn: '<path d="M9 14L4 9l5-5"/><path d="M4 9h10.5a5.5 5.5 0 0 1 0 11H11"/>',
  inbox: '<path d="M3.5 13.5l2.6-7.8a1 1 0 0 1 1-.7h9.8a1 1 0 0 1 1 .7l2.6 7.8V19a1 1 0 0 1-1 1h-15a1 1 0 0 1-1-1z"/><path d="M3.5 13.5H8l1.5 2.5h5l1.5-2.5h4.5"/>',
};
const ic = (name, cls = "") => `<svg class="icon ${cls}" viewBox="0 0 24 24" aria-hidden="true">${ICONS[name] || ""}</svg>`;

const KIND_LABELS = {
  root: "Investigation", io: "Load", check: "Data quality", retrieval: "Retrieval",
  playbook: "Playbook", llm: "Model", step: "Playbook step", score: "Confidence",
  policy: "HITL policy", human: "Human", report: "Report",
};

function esc(v) {
  return String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
const kindColor = (k) => `var(--k-${k}, var(--k-io))`;
const sevPill = (s) => s ? `<span class="sev sev-${esc(s)}">${esc(s)}</span>` : "—";
const badge = (s, text) => s || text ? `<span class="badge ${esc(s)}">${esc(text ?? s.replaceAll("_", " "))}</span>` : "";
const json = (v) => `<pre>${esc(JSON.stringify(v, null, 2))}</pre>`;
const plural = (n, word, many = `${word}s`) => `${n} ${n === 1 ? word : many}`;
const cap = (s) => s ? s[0].toUpperCase() + s.slice(1) : s;
const pbLink = (slug, text = slug) => `<a href="#" class="pb-link" data-playbook="${esc(slug)}">${ic("book")}${esc(text)}</a>`;

// Collapsible pieces whose open/closed state survives re-renders.
const isOpen = (key, dflt) => state.open[key] ?? dflt;
function row(key, icon, tint, title, preview, body, defaultOpen = false) {
  return `<details class="row" data-key="${esc(key)}" ${isOpen(key, defaultOpen) ? "open" : ""}>
    <summary><span class="row-tile tint-${tint}">${ic(icon)}</span><span class="row-title">${title}</span>
      <span class="row-preview">${preview}</span>${ic("chevron", "chevron")}</summary>
    <div class="row-body">${body}</div>
  </details>`;
}
function disclosure(key, title, body, defaultOpen = false) {
  return `<details class="disclosure" data-key="${esc(key)}" ${isOpen(key, defaultOpen) ? "open" : ""}>
    <summary>${ic("chevron", "chevron")}${title}</summary>${body}
  </details>`;
}
document.addEventListener("toggle", (e) => {
  const key = e.target.dataset?.key;
  if (key) state.open[key] = e.target.open;
}, true);

function reviewer() {
  try { return localStorage.getItem("reviewer") || "analyst"; } catch { return "analyst"; }
}
function setReviewer(v) {
  try { localStorage.setItem("reviewer", v); } catch {}
}

async function api(path, opts = {}) {
  const res = await fetch(path, { headers: { "Content-Type": "application/json" }, ...opts });
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.statusText);
  return res.json();
}

// ---------- Health ----------
async function loadHealth() {
  const h = await api("/api/health");
  const chip = (led, text, title = "") => `<span class="chip" title="${esc(title)}"><span class="led ${led}"></span>${esc(text)}</span>`;
  // Only problems are shown in the toolbar.
  $("#health").innerHTML = h.step_rule_problems.map((p) => chip("bad", "Step overlay out of sync", p)).join("");
}

// ---------- Alert picker (search box + dropdown) ----------
const picker = { open: false, origin: "", active: 0, matches: [] };

async function loadAlerts() {
  state.alerts = await api("/api/alerts");
  renderPicker();
}

function highlight(text, q) {
  const safe = esc(text);
  if (!q) return safe;
  const i = text.toLowerCase().indexOf(q);
  return i < 0 ? safe : `${esc(text.slice(0, i))}<mark>${esc(text.slice(i, i + q.length))}</mark>${esc(text.slice(i + q.length))}`;
}

function renderPicker() {
  const q = $("#search").value.trim().toLowerCase();
  picker.matches = state.alerts.filter((a) =>
    (!picker.origin || a.origin === picker.origin) &&
    (!q || `${a.alert_id} ${a.description} ${a.source_system} ${a.affected_user} ${a.affected_device}`.toLowerCase().includes(q)));
  picker.active = Math.min(picker.active, Math.max(picker.matches.length - 1, 0));
  $("#alert-count").textContent = plural(picker.matches.length, "alert");
  document.querySelectorAll("#origin button").forEach((b) => b.classList.toggle("active", b.dataset.origin === picker.origin));
  $("#alerts").innerHTML = picker.matches.length ? picker.matches.map((a, i) => `
    <li class="opt ${i === picker.active ? "active" : ""} ${state.selected === a.alert_id ? "current" : ""}" role="option" data-id="${esc(a.alert_id)}" data-index="${i}">
      <div class="opt-main">
        <div class="opt-top"><span class="id">${highlight(a.alert_id, q)}</span><span class="meta">${esc(a.source_system)} · ${esc(a.timestamp.slice(0, 10))}</span></div>
        <div class="desc">${highlight(a.description, q)}</div>
      </div>
      <div class="opt-side">${a.last_run ? badge(a.last_run.status) : ""}${sevPill(a.severity)}</div>
    </li>`).join("") : `<li class="picker-empty">No alerts match “${esc(q)}”.</li>`;
  $("#alerts .opt.active")?.scrollIntoView({ block: "nearest" });
}

function setPickerOpen(open) {
  if (open && !picker.open && state.selected) {
    // Start the keyboard highlight on the alert that is open now.
    const q = $("#search").value.trim();
    if (!q) picker.active = Math.max(0, state.alerts.filter((a) => !picker.origin || a.origin === picker.origin).findIndex((a) => a.alert_id === state.selected));
  }
  picker.open = open;
  $(".home")?.classList.toggle("searching", open);
  $("#picker").classList.toggle("open", open);
  $("#picker-menu").hidden = !open;
  $("#search").setAttribute("aria-expanded", String(open));
  if (open) renderPicker();
}

$("#picker-toggle").addEventListener("click", () => {
  setPickerOpen(!picker.open);
  if (picker.open) $("#search").focus();
});
$("#search").addEventListener("focus", () => { if ($("#search").value) setPickerOpen(true); });
$("#search").addEventListener("input", () => { picker.active = 0; setPickerOpen(true); });
$("#search").addEventListener("keydown", (e) => {
  if (e.key === "ArrowDown" || e.key === "ArrowUp") {
    e.preventDefault();
    if (!picker.open) return setPickerOpen(true);
    picker.active = (picker.active + (e.key === "ArrowDown" ? 1 : -1) + picker.matches.length) % Math.max(picker.matches.length, 1);
    renderPicker();
  } else if (e.key === "Enter" && picker.open && picker.matches[picker.active]) {
    e.preventDefault();
    chooseAlert(picker.matches[picker.active].alert_id);
  } else if (e.key === "Escape") {
    setPickerOpen(false);
  }
});
$("#alerts").addEventListener("mousedown", (e) => {
  const opt = e.target.closest(".opt");
  if (opt) { e.preventDefault(); chooseAlert(opt.dataset.id); }
});
$("#origin").addEventListener("click", (e) => {
  const b = e.target.closest("button");
  if (b) { picker.origin = b.dataset.origin; picker.active = 0; renderPicker(); }
});
document.addEventListener("mousedown", (e) => { if (picker.open && !$("#picker").contains(e.target)) setPickerOpen(false); });
$("#simulate").addEventListener("click", async () => {
  $("#simulate").disabled = true;
  try {
    await api("/api/simulate", { method: "POST", body: JSON.stringify({ count: 10, novel_ratio: 0.25 }) });
    picker.origin = "simulator";
    await loadAlerts();
  } finally { $("#simulate").disabled = false; }
});
$("#clear-sim").addEventListener("click", async () => {
  await api("/api/simulate", { method: "DELETE" });
  picker.origin = "";
  await loadAlerts();
});

function chooseAlert(id) {
  $("#search").value = "";
  setPickerOpen(false);
  $("#search").blur();
  selectAlert(id);
}

// The same picker lives centred on the home screen and in the toolbar once an alert is open.
function placePicker(home) {
  const slot = home ? $("#home-slot") : $("#toolbar-slot");
  if (slot && $("#picker").parentElement !== slot) slot.appendChild($("#picker"));
  $("#search").placeholder = home ? "Search alerts by ID, user, host or description" : "Search or switch alert";
}

$("#home").addEventListener("click", (e) => {
  e.preventDefault();
  clearInterval(state.poll);
  if (!confirmLeavePlaybook()) return;
  state.selected = null;
  state.run = null;
  state.view = "run";
  history.replaceState(null, "", location.pathname);
  renderHome();
});

// ---------- Selection & runs ----------
async function selectAlert(id) {
  if (!confirmLeavePlaybook()) return;
  state.view = "run";
  state.selected = id;
  state.spanId = null;
  history.replaceState(null, "", `#${encodeURIComponent(id)}`);
  const alert = state.alerts.find((a) => a.alert_id === id);
  state.run = alert?.last_run ? await api(`/api/runs/${alert.last_run.run_id}`) : null;
  render();
  watchRun();
}

async function startRun() {
  state.run = await api("/api/runs", { method: "POST", body: JSON.stringify({ alert_id: state.selected }) });
  state.tab = "trace";
  state.spanId = null;
  render();
  watchRun();
}

function watchRun() {
  clearInterval(state.poll);
  if (state.run?.status !== "running") return;
  state.poll = setInterval(async () => {
    state.run = await api(`/api/runs/${state.run.run_id}`);
    if (state.run.status !== "running") {
      clearInterval(state.poll);
      state.tab = "report";
      loadAlerts();
    }
    if (state.view === "run") render();  // don't rebuild the playbook editor under the cursor
  }, 1200);
}

// ---------- Main view ----------
function renderHome() {
  const investigated = state.alerts.filter((a) => a.last_run).length;
  const waiting = state.alerts.filter((a) => a.last_run?.status === "awaiting_human").length;
  $("#main").innerHTML = `
    <div class="home">
      <div class="home-mark" data-logo></div>
      <h1>SOC Triage Agent</h1>
      <p class="tagline">Pick an alert to triage. The agent investigates; you approve what matters.</p>
      <div id="home-slot" class="home-slot"></div>
      <div class="home-stats">
        <span class="chip">${plural(state.alerts.length, "alert")}</span>
        <span class="chip">${investigated} investigated</span>
        ${waiting ? `<span class="chip"><span class="led warn"></span>${waiting} awaiting review</span>` : ""}
      </div>
    </div>`;
  placePicker(true);
  fillLogos();
}

function render() {
  const alert = state.alerts.find((a) => a.alert_id === state.selected) || state.run?.alert;
  if (!alert) return renderHome();
  placePicker(false);
  if (state.view === "playbook") return renderPlaybookPage();
  const run = state.run;
  const running = run?.status === "running";
  const button = running
    ? `<button disabled>${ic("clock")}Investigating…</button>`
    : run ? `<button id="run-btn" class="secondary">${ic("refresh")}Re-run</button>`
    : `<button id="run-btn">${ic("play")}Investigate</button>`;
  $("#main").innerHTML = `
    <div class="content">
      <div class="card alert-head">
        <div>
          <div class="title">${esc(alert.alert_id)} ${sevPill(alert.severity)} <span class="label">reported</span></div>
          <div class="desc">${esc(alert.description)}</div>
          <div class="facts">
            <span>${ic("server")}<b>${esc(alert.source_system)}</b></span>
            <span>${ic("person")}<b>${esc(alert.affected_user)}</b></span>
            <span>${ic("desktop")}<b>${esc(alert.affected_device)}</b></span>
            <span>${ic("clock")}<b>${esc(alert.timestamp.replace("T", " ").replace("Z", " UTC"))}</b></span>
            <span>${ic("inbox")}${esc(alert.origin === "csv" ? "CSV feed" : "Simulated")}</span>
          </div>
        </div>
        ${button}
      </div>
      ${run ? renderRun(run) : `<div class="empty">${ic("play")}Not investigated yet.</div>`}
    </div>`;
  $("#run-btn")?.addEventListener("click", startRun);
  bindRunEvents();
}

function confidenceRing(score) {
  const r = 13, c = 2 * Math.PI * r;
  return `<svg viewBox="0 0 34 34" aria-hidden="true"><circle class="track" cx="17" cy="17" r="${r}"/>
    <circle class="fill" cx="17" cy="17" r="${r}" stroke-dasharray="${c}" stroke-dashoffset="${c * (1 - score / 100)}"/></svg>`;
}

function renderRun(run) {
  const inv = run.investigation;
  const conf = run.confidence;
  const fa = run.final_action || {};
  const pending = run.gates.filter((g) => g.status === "pending").length;
  const banners = [
    run.error ? `<div class="banner bad">${ic("warning")}<div><b>Run failed.</b> ${esc(run.error)}</div></div>` : "",
    ...(run.policy_violations || []).map((v) => `<div class="banner bad">${ic("hand")}<div><b>Policy:</b> ${esc(v)}</div></div>`),
    conf?.preface ? `<div class="banner info">${ic("sparkles")}<div><b>${esc(conf.preface)}</b> No close historical match, so treat this as a first look.</div></div>` : "",
  ].join("");
  const tile = (icon, label, value, sub = "") => `<div class="tile"><div class="label">${ic(icon)}${label}</div><div class="value">${value}</div><div class="sub">${sub}</div></div>`;
  const tabs = [["report", "doc", "Report"], ["approvals", "checkCircle", "Approvals"], ["trace", "timeline", "Trace"]];
  return `
    ${banners}
    <div class="summary">
      ${tile("clock", "Status", badge(run.status), esc(new Date(run.created_at).toLocaleString()))}
      ${tile("tag", "Incident type", esc(inv?.incident_type ?? "—"), esc((run.playbooks || []).map((p) => p.slug).join(", ") || "No playbook"))}
      ${tile("warning", "Severity", inv ? sevPill(inv.assessed_severity) : "—", `Reported ${esc(run.alert.severity)}`)}
      <div class="tile"><div class="label">${ic("gauge")}Confidence</div>
        ${conf ? `<div class="ring">${confidenceRing(conf.score)}<div><div class="value" style="margin:0">${conf.score}</div><div class="sub">${esc(cap(conf.band))}</div></div></div>` : `<div class="value">—</div>`}
      </div>
      ${tile("bolt", "Action", esc(cap(fa.action ?? inv?.recommended_action) ?? "—"), esc(fa.note ?? ""))}
    </div>
    <div class="segmented-row">
      <div class="segmented" role="tablist">
        ${tabs.map(([t, icon, label]) => `<button class="${state.tab === t ? "active" : ""}" data-tab="${t}" role="tab">${ic(icon)}${label}${t === "approvals" && pending ? `<span class="count">${pending}</span>` : ""}</button>`).join("")}
      </div>
      ${state.tab === "report" && run.report ? `<span>
        <button class="plain small" data-expand="all">Expand all</button>
        <button class="plain small" data-expand="none">Collapse all</button>
        <a class="small" href="/api/runs/${esc(run.run_id)}/report.md" target="_blank" style="margin-left:6px">${ic("export")} Export</a></span>` : ""}
    </div>
    <div id="tab-body">${state.tab === "trace" ? renderTrace(run) : state.tab === "approvals" ? renderApprovals(run) : renderReport(run)}</div>`;
}

function bindRunEvents() {
  document.querySelectorAll("[data-tab]").forEach((b) => b.addEventListener("click", () => { state.tab = b.dataset.tab; render(); }));
  document.querySelectorAll(".span-row").forEach((r) => r.addEventListener("click", () => { state.spanId = r.dataset.id; render(); }));
  document.querySelectorAll("[data-gate]").forEach((b) => b.addEventListener("click", () => decide(b.dataset.gate, b.dataset.decision)));
  document.querySelectorAll("[data-playbook]").forEach((a) => a.addEventListener("click", (e) => { e.preventDefault(); openPlaybook(a.dataset.playbook); }));
  document.querySelectorAll("[data-goto-tab]").forEach((b) => b.addEventListener("click", () => { state.tab = b.dataset.gotoTab; render(); window.scrollTo(0, 0); }));
  document.querySelectorAll("[data-expand]").forEach((b) => b.addEventListener("click", () => {
    const open = b.dataset.expand === "all";
    document.querySelectorAll("#tab-body details.row").forEach((d) => { d.open = open; state.open[d.dataset.key] = open; });
  }));
  const rv = $("#reviewer");
  if (rv) rv.addEventListener("change", () => setReviewer(rv.value));
}

// ---------- Report ----------
function renderReport(run) {
  const r = run.report;
  if (!r) return `<div class="empty">${ic("doc")}The report appears when the run finishes.</div>`;
  const inv = run.investigation;
  const conf = r.confidence;
  const www = r.what_went_wrong;
  const fa = r.final_action || {};
  const list = (items) => items.length ? `<ul>${items.map((i) => `<li>${esc(i)}</li>`).join("")}</ul>` : `<p class="muted">None</p>`;

  const steps = r.steps;
  const humanSteps = steps.filter((s) => s.owner === "human").length;
  const gapSteps = steps.filter((s) => s.status === "evidence_unavailable").length;
  const issues = www.evidence_gaps.length + www.data_quality_flags.length + www.policy_violations.length;
  const pending = r.human_decisions.filter((d) => d.status === "pending").length;
  const usage = r.trace_summary.usage || {};
  const hist = r.historical_incidents;

  const decision = [
    row("r:action", "bolt", "red", "Recommended action", esc(cap(r.recommended_action.action) ?? ""), `
      <p>${esc(r.recommended_action.rationale ?? "")}</p>
      <span class="label">Next actions</span>${list(r.next_actions)}
      <span class="label">Final</span><p>${esc(cap(fa.action) ?? "Pending")}${fa.by ? ` · ${esc(fa.by)}` : ""}${fa.note ? ` — ${esc(fa.note)}` : ""}</p>`, true),
    row("r:class", "tag", "blue", "Classification", `${esc(r.incident_type ?? "—")} · ${esc(r.severity.reported)} → ${esc(r.severity.assessed ?? "—")}`, `
      <span class="label">Type</span><p>${esc(inv?.classification_rationale ?? "—")}</p>
      <span class="label">Severity</span><p>${esc(r.severity.rationale ?? "—")}</p>`),
    conf ? row("r:conf", "gauge", "indigo", "Confidence", `${conf.score} · ${esc(cap(conf.band))}`, `
      <table><tr><th>Factor</th><th>Detail</th><th class="num">Effect</th></tr>
      ${conf.factors.map((f) => `<tr><td>${esc(cap(f.factor.replaceAll("_", " ")))}</td><td>${esc(f.detail)}</td><td class="num ${f.delta < 0 ? "neg" : f.delta > 0 ? "pos" : ""}">${f.delta > 0 ? "+" : ""}${f.delta}</td></tr>`).join("")}</table>`) : "",
  ].join("");

  const evidence = [
    row("r:steps", "list", "teal", "Investigation steps", `${plural(steps.length, "step")} · ${humanSteps} human · ${plural(gapSteps, "gap")}`, steps.length ? `
      <table><tr><th>Phase</th><th>Playbook step</th><th>Finding</th><th>Owner</th><th>Status</th></tr>
      ${steps.map((s) => `<tr>
        <td>${esc(s.phase)}</td>
        <td>${pbLink(s.playbook)}<div class="muted small">${esc(s.playbook_quote)}</div></td>
        <td>${esc(s.finding)}<div class="mono muted">${esc(s.evidence.join(", "))}</div></td>
        <td>${badge(s.owner)}</td><td>${badge(s.status)}</td></tr>`).join("")}</table>` : `<p class="muted">No steps.</p>`),
    row("r:wrong", "warning", "orange", "What went wrong", plural(issues, "issue"), `
      <span class="label">Evidence gaps</span>${list(www.evidence_gaps)}
      <span class="label">Data quality</span>${list(www.data_quality_flags.map((f) => `${f.code}: ${f.message}`))}
      ${www.policy_violations.length ? `<span class="label">Policy</span>${list(www.policy_violations)}` : ""}`),
    row("r:history", "history", "gray", "Historical incidents", hist.length ? `${plural(hist.length, "match", "matches")} · top ${hist[0].score.toFixed(2)}` : "None", hist.length ? `
      <table><tr><th>Incident</th><th>Type</th><th>Circumstances</th><th>Outcome</th><th class="num">Similarity</th></tr>
      ${hist.map((m) => `<tr><td class="mono">${esc(m.incident.incident_id)}</td><td>${esc(m.incident.alert_type)}</td><td>${esc(m.incident.circumstances)}</td><td>${esc(m.incident.outcome)}</td><td class="num">${m.score.toFixed(2)}</td></tr>`).join("")}</table>` : `<p class="muted">No similar incidents.</p>`),
    row("r:playbooks", "book", "brown", "Playbooks consulted", esc(r.playbooks_consulted.map((p) => p.slug).join(", ") || "None"),
      r.playbooks_consulted.length ? `<div class="pb-cards">${r.playbooks_consulted.map((p, i) => `
        <a href="#" class="pb-card" data-playbook="${esc(p.slug)}">
          <span class="row-tile tint-brown">${ic("book")}</span>
          <span class="grow"><b>${esc(p.alert_type)}</b><span class="muted small">${esc(p.path)} · ${i === 0 ? "primary" : "secondary"}${p.origin !== "official" ? " · AI-drafted" : ""}</span></span>
          <span class="small">Open</span>${ic("chevron", "chevron")}
        </a>`).join("")}</div>` : `<p class="muted">No playbook matched, so the agent treated this alert as novel.</p>`, true),
  ].join("");

  const audit = [
    row("r:decisions", "person", "green", "Human decisions", r.human_decisions.length ? `${pending} pending · ${r.human_decisions.length - pending} decided` : "None needed", r.human_decisions.length ? `
      <table><tr><th>Gate</th><th>Status</th><th>Reviewer</th><th>Reason</th></tr>
      ${r.human_decisions.map((d) => `<tr><td>${esc(d.gate)}</td><td>${badge(d.status)}</td><td>${esc(d.reviewer ?? "—")}</td><td>${esc(d.reason ?? "")}</td></tr>`).join("")}</table>` : `<p class="muted">Nothing needed a person.</p>`),
  ].join("");

  return `
    <div class="group-title">Decision</div><div class="group">${decision}</div>
    <div class="group-title">Evidence</div><div class="group">${evidence}</div>
    <div class="group-title">Audit</div><div class="group">${audit}</div>
    <div class="group-title">Trace &amp; model usage</div>${renderUsageCard(run)}`;
}

function renderUsageCard(run) {
  const spans = run.trace;
  const root = spans.find((s) => s.kind === "root");
  const llm = spans.find((s) => s.kind === "llm");
  const usage = llm?.attributes?.usage || {};
  const dur = (s) => s?.end ? s.end - s.start : null;
  const fmt = (ms) => ms == null ? "—" : ms >= 60000 ? `${(ms / 60000).toFixed(1)}m` : ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${Math.round(ms)}ms`;
  const num = (n) => n == null ? "—" : Number(n).toLocaleString();
  const hasTokens = usage.input_tokens != null;
  const promptTokens = hasTokens ? usage.input_tokens + usage.cache_read_input_tokens + usage.cache_creation_input_tokens : null;
  const hitRate = hasTokens && promptTokens ? `${Math.round((usage.cache_read_input_tokens / promptTokens) * 100)}%` : "—";
  const humans = spans.filter((s) => s.kind === "human");
  const stat = (label, value, sub = "") => `<div class="mstat"><div class="label">${label}</div><div class="value">${value}</div><div class="sub">${sub}</div></div>`;
  return `
    <div class="card usage">
      <div class="mstats">
        ${stat("Agent time", fmt(dur(root)), plural(spans.length, "span"))}
        ${stat("Model call", fmt(dur(llm)), run.llm_backend === "claude" ? esc(llm?.attributes?.model ?? "—") : "")}
        ${stat("Prompt tokens", num(promptTokens), hasTokens ? `${num(usage.input_tokens)} uncached` : "not reported")}
        ${stat("Cache hit", hitRate, hasTokens ? `${num(usage.cache_read_input_tokens)} read · ${num(usage.cache_creation_input_tokens)} written` : "")}
        ${stat("Output tokens", num(usage.output_tokens), "")}
        ${stat("Human gates", humans.length, `${humans.filter((s) => s.status === "waiting").length} waiting`)}
      </div>
      <div class="usage-foot">
        <span class="muted small">${llm?.attributes?.request_id ? `Request <span class="mono">${esc(llm.attributes.request_id)}</span>` : hasTokens ? "" : "Token usage was not reported for this run."}</span>
        <button class="secondary" data-goto-tab="trace">${ic("timeline")}Open full trace</button>
      </div>
    </div>`;
}

// ---------- Trace ----------
function orderSpans(spans) {
  const children = {};
  spans.forEach((s) => (children[s.parent_id ?? "root"] ||= []).push(s));
  const out = [];
  const walk = (parent, depth) => (children[parent] || []).sort((a, b) => a.start - b.start).forEach((s) => {
    out.push({ ...s, depth });
    walk(s.span_id, depth + 1);
  });
  walk("root", 0);
  return out;
}

function renderTrace(run) {
  const spans = orderSpans(run.trace);
  if (!spans.length) return `<div class="empty">${ic("timeline")}Starting…</div>`;
  const now = Date.now();
  const fmt = (ms) => ms >= 3600000 ? `${(ms / 3600000).toFixed(1)}h` : ms >= 60000 ? `${(ms / 60000).toFixed(1)}m` : ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${Math.round(ms)}ms`;

  // The axis covers the agent's own work. Human waits can last hours, so they get
  // a fixed zone on the right instead of stretching the scale.
  const agent = spans.filter((s) => s.kind !== "human");
  const humans = spans.filter((s) => s.kind === "human");
  const AGENT_ZONE = humans.length ? 78 : 100;
  const t0 = Math.min(...spans.map((s) => s.start));
  const t1 = Math.max(...agent.map((s) => s.end ?? now), t0 + 1);
  const total = t1 - t0;
  const pct = (t) => Math.min(((t - t0) / total) * AGENT_ZONE, AGENT_ZONE);

  const ticks = [0, 0.25, 0.5, 0.75, 1].map((f) => `<span style="left:${f * AGENT_ZONE}%">${fmt(f * total)}</span>`).join("")
    + (humans.length ? `<span style="left:${(AGENT_ZONE + 100) / 2}%">Human review</span>` : "");
  const rows = spans.map((s) => {
    const end = s.end ?? now;
    const dur = end - s.start;
    const color = kindColor(s.kind);
    const left = pct(s.start);
    const width = s.kind === "human" ? 100 - left : Math.max((dur / total) * AGENT_ZONE, 0.3);
    const label = s.kind === "human" ? `${s.status === "waiting" ? "waiting" : esc(s.status)} ${fmt(dur)}` : width > 7 ? fmt(dur) : "";
    const mark = s.kind === "step" || (dur === 0 && s.kind !== "human")
      ? `<div class="marker" style="left:${left}%;background:${color}" title="${esc(s.name)}"></div>`
      : `<div class="bar ${s.status === "waiting" || s.status === "running" ? "waiting" : ""} ${s.status === "error" ? "error" : ""}"
             style="left:${left}%;width:${width}%;background:${color}" title="${esc(fmt(dur))}">${label}</div>`;
    return `
      <div class="span-row ${state.spanId === s.span_id ? "active" : ""}" data-id="${s.span_id}">
        <div class="span-name" style="padding-left:${12 + s.depth * 14}px" title="${esc(s.name)}">
          <span class="dot" style="background:${color}"></span>${esc(s.name)}
          ${s.status === "waiting" ? badge("awaiting_human", "waiting") : ""}
          ${s.status === "error" ? badge("failed", "error") : ""}
        </div>
        <div class="span-track">${mark}</div>
      </div>`;
  }).join("");

  // Share of the agent's time by kind, like an APM service breakdown. Human waits are reported separately.
  const byKind = {};
  agent.filter((s) => s.kind !== "root" && s.kind !== "step").forEach((s) => { byKind[s.kind] = (byKind[s.kind] || 0) + ((s.end ?? now) - s.start); });
  const sum = Object.values(byKind).reduce((a, b) => a + b, 0) || 1;
  const legend = Object.entries(byKind).filter(([, v]) => v > 0).sort((a, b) => b[1] - a[1]).map(([k, v]) => `
    <div class="legend-row"><span class="dot" style="background:${kindColor(k)}"></span><span>${esc(KIND_LABELS[k] || k)}</span><span class="muted">${((v / sum) * 100).toFixed(1)}%</span>
      <div class="legend-bar"><div style="width:${(v / sum) * 100}%;background:${kindColor(k)}"></div></div></div>`).join("");
  const waiting = humans.filter((s) => s.status === "waiting").length;
  const humanCard = humans.length ? `
    <div class="legend"><span class="label">Human review</span>
      <div class="kv-row"><span>Agent time</span><span>${fmt(total)}</span></div>
      <div class="kv-row"><span>Waiting</span><span>${waiting} of ${humans.length}</span></div>
      <div class="kv-row"><span>Longest wait</span><span>${fmt(Math.max(...humans.map((s) => (s.end ?? now) - s.start)))}</span></div>
    </div>` : "";
  const usage = run.trace.find((s) => s.kind === "llm")?.attributes?.usage || {};
  const usageCard = usage.input_tokens != null ? `
    <div class="legend"><span class="label">Model tokens</span>
      ${[["Input", usage.input_tokens], ["Cache read", usage.cache_read_input_tokens], ["Cache write", usage.cache_creation_input_tokens], ["Output", usage.output_tokens]]
        .map(([k, v]) => `<div class="kv-row"><span>${k}</span><span>${v}</span></div>`).join("")}
    </div>` : "";

  const selected = run.trace.find((s) => s.span_id === state.spanId);
  return `
    <div class="trace">
      <div class="waterfall">
        <div class="axis"><div class="span-name">Span</div><div class="ticks">${ticks}</div></div>
        ${rows}
      </div>
      <div class="side"><div class="legend"><span class="label">Agent time by kind</span>${legend}</div>${humanCard}${usageCard}</div>
    </div>
    ${selected ? renderSpanDetail(selected) : `<p class="muted small" style="margin-left:4px">Select a span to see its inputs, outputs and attributes.</p>`}`;
}

function renderSpanDetail(s) {
  const out = s.output || {};
  const dur = s.end ? `${Math.round(s.end - s.start)} ms` : "in progress";
  const subs = [
    s.kind === "llm" && out.reasoning_summary ? disclosure("s:reasoning", "Model reasoning (summary)", `<div class="reasoning">${esc(out.reasoning_summary)}</div>`, true) : "",
    s.output != null ? disclosure("s:output", "Output", json(s.output), true) : "",
    s.input != null ? disclosure("s:input", "Input", json(s.input)) : "",
    disclosure("s:attrs", "Attributes", json(s.attributes)),
  ].join("");
  return `
    <div class="card detail">
      <div class="detail-head">
        <h3><span class="dot" style="background:${kindColor(s.kind)}"></span>${esc(s.name)}</h3>
        <div class="facts"><span>Kind <b>${esc(KIND_LABELS[s.kind] || s.kind)}</b></span><span>Status <b>${esc(s.status)}</b></span><span>${ic("clock")}<b>${dur}</b></span><span class="mono">${esc(s.span_id)}</span></div>
      </div>
      <div class="subs">${subs}</div>
    </div>`;
}

// ---------- Approvals ----------
function renderDiff(diff) {
  return `<pre class="diff">${diff.split("\n").map((l) => {
    const cls = l.startsWith("@@") ? "hunk" : l.startsWith("+") && !l.startsWith("+++") ? "add" : l.startsWith("-") && !l.startsWith("---") ? "del" : "";
    return `<span class="${cls}">${esc(l)}</span>`;
  }).join("")}</pre>`;
}

const GATE_STYLE = {
  action_approval: ["bolt", "red"],
  act_then_confirm: ["checkCircle", "orange"],
  playbook_step: ["person", "blue"],
  playbook_proposal: ["book", "brown"],
};

function renderApprovals(run) {
  if (!run.gates.length) return `<div class="empty">${ic("checkCircle")}Nothing needs a person for this run.</div>`;
  const head = `<div class="reviewer">${ic("person")}<span class="small">Reviewer</span><input id="reviewer" value="${esc(reviewer())}"></div>`;
  const order = (g) => (g.status === "pending" ? 0 : 1) + (g.blocking ? 0 : 0.5);
  return head + [...run.gates].sort((a, b) => order(a) - order(b)).map((g) => {
    const decided = g.status !== "pending";
    const d = g.decision;
    const [icon, tint] = GATE_STYLE[g.kind] || ["checkCircle", "gray"];
    const outcome = decided ? `<div class="outcome">${ic(g.status === "denied" ? "xmark" : "check")}<b>${esc(cap(g.status))}</b> by ${esc(d.reviewer)}${d.reason ? ` — ${esc(d.reason)}` : ""}${d.action_override ? ` · action → ${esc(d.action_override)}` : ""}${d.written_to ? ` · saved to <span class="mono">${esc(d.written_to)}</span>` : ""}</div>` : "";
    const reason = `<input id="reason-${g.gate_id}" placeholder="Reason or notes">`;
    let body = "", actions = "";
    if (g.kind === "action_approval") {
      body = `<div>Agent recommends <b>${esc(g.payload.action)}</b> at ${sevPill(g.payload.severity)}</div>`;
      actions = `${reason}
        <select id="override-${g.gate_id}" aria-label="Alternative action">${["monitor", "isolate", "escalate", "close"].map((a) => `<option ${a === g.payload.action ? "selected" : ""}>${a}</option>`).join("")}</select>
        <button class="secondary" data-gate="${g.gate_id}" data-decision="modify">Use selected</button>
        <button class="destructive" data-gate="${g.gate_id}" data-decision="deny">Reject</button>
        <button data-gate="${g.gate_id}" data-decision="approve">${ic("check")}Approve</button>`;
    } else if (g.kind === "act_then_confirm") {
      body = `<div>The agent's <b>${esc(g.payload.action)}</b> recommendation stands immediately. Confirm or reverse it.</div>`;
      actions = `${reason}<button class="destructive" data-gate="${g.gate_id}" data-decision="deny">${ic("arrowUturn")}Reverse</button><button data-gate="${g.gate_id}" data-decision="approve">${ic("check")}Confirm</button>`;
    } else if (g.kind === "playbook_step") {
      body = `<div class="quote">${esc(g.payload.quote)}</div><div class="small muted">From ${pbLink(g.payload.playbook)}</div>`;
      actions = `${reason}<button class="destructive" data-gate="${g.gate_id}" data-decision="deny">Could not complete</button><button data-gate="${g.gate_id}" data-decision="approve">${ic("check")}Done</button>`;
    } else if (g.kind === "playbook_proposal") {
      const p = g.payload.proposal;
      body = `<div class="small muted" style="margin-bottom:6px">${esc(cap(p.kind.replace("_", " ")))}${p.target_playbook ? ` for <span class="mono">${esc(p.target_playbook)}</span>` : ""}. Approved drafts are saved to <span class="mono">playbook_proposals/approved/</span>; official playbooks are never changed.</div>
        ${disclosure(`g:${g.gate_id}:diff`, "Proposed changes", renderDiff(g.payload.diff), !decided)}
        ${decided ? "" : disclosure(`g:${g.gate_id}:edit`, "Edit before approving", `<textarea class="editor" id="edit-${g.gate_id}">${esc(p.markdown)}</textarea>`)}`;
      actions = `${reason}<button class="destructive" data-gate="${g.gate_id}" data-decision="deny">Deny</button><button class="secondary" data-gate="${g.gate_id}" data-decision="modify">Approve with edits</button><button data-gate="${g.gate_id}" data-decision="approve">${ic("check")}Approve</button>`;
    }
    return `
      <div class="card gate ${decided ? "done" : ""}">
        <div class="gate-head">
          <span class="row-tile tint-${decided ? "gray" : tint}">${ic(icon)}</span>
          <div class="grow"><h4>${esc(g.title)}</h4><div class="why">${esc(g.reason)}</div></div>
          ${g.blocking && !decided ? badge("failed", "Blocking") : badge("", decided ? cap(g.status) : "Follow-up")}
        </div>
        <div class="body">${body}</div>
        ${decided ? outcome : `<div class="actions">${actions}</div>`}
      </div>`;
  }).join("");
}

async function decide(gateId, decision) {
  const body = { decision, reviewer: $("#reviewer")?.value || reviewer(), reason: $(`#reason-${gateId}`)?.value || "" };
  const override = $(`#override-${gateId}`);
  if (override && decision === "modify") body.action_override = override.value;
  const editor = $(`#edit-${gateId}`);
  if (editor && decision === "modify") body.edited_markdown = editor.value;
  setReviewer(body.reviewer);
  try {
    state.run = await api(`/api/runs/${state.run.run_id}/gates/${gateId}`, { method: "POST", body: JSON.stringify(body) });
    render();
    loadAlerts();
  } catch (e) {
    window.alert(`Could not save decision: ${e.message}`);
  }
}

// ---------- Playbook viewer / editor ----------
function renderMarkdown(md) {
  const inline = (t) => esc(t)
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/(^|[\s(])\*([^*\s][^*]*)\*/g, "$1<em>$2</em>")
    .replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
  const out = [];
  let para = [], list = null, code = null;
  const flushPara = () => { if (para.length) out.push(`<p>${inline(para.join(" "))}</p>`); para = []; };
  const flushList = () => { if (list) out.push(`<${list.tag}>${list.items.map((i) => `<li>${inline(i)}</li>`).join("")}</${list.tag}>`); list = null; };
  for (const line of md.replace(/<!--([\s\S]*?)-->/g, (_, c) => `\n%%NOTE%%${c.trim().replace(/\n/g, " ")}\n`).split("\n")) {
    if (code) {
      if (line.trim().startsWith("```")) { out.push(`<pre>${esc(code.join("\n"))}</pre>`); code = null; } else code.push(line);
      continue;
    }
    if (line.trim().startsWith("```")) { flushPara(); flushList(); code = []; continue; }
    if (line.startsWith("%%NOTE%%")) { flushPara(); flushList(); out.push(`<div class="md-note">${ic("sparkles")}${esc(line.slice(8))}</div>`); continue; }
    const h = line.match(/^(#{1,4})\s+(.*)$/);
    if (h) { flushPara(); flushList(); out.push(`<h${h[1].length}>${inline(h[2])}</h${h[1].length}>`); continue; }
    const li = line.match(/^\s*(?:([-*])|(\d+)\.)\s+(.*)$/);
    if (li) {
      flushPara();
      const tag = li[2] ? "ol" : "ul";
      if (!list || list.tag !== tag) { flushList(); list = { tag, items: [] }; }
      list.items.push(li[3]);
      continue;
    }
    if (!line.trim()) { flushPara(); flushList(); continue; }
    if (list && /^\s+/.test(line)) { list.items[list.items.length - 1] += ` ${line.trim()}`; continue; }
    flushList();
    para.push(line.trim());
  }
  flushPara(); flushList();
  if (code) out.push(`<pre>${esc(code.join("\n"))}</pre>`);
  return out.join("\n");
}

const playbookHash = (slug) => `#${encodeURIComponent(state.selected)}/playbook/${slug.split("/").map(encodeURIComponent).join("/")}`;
const playbookDirty = () => state.view === "playbook" && state.playbook?.data && state.playbook.draft !== state.playbook.data.text;

function confirmLeavePlaybook() {
  if (!playbookDirty()) return true;
  if (!window.confirm("You have unsaved changes to this playbook. Leave without saving?")) return false;
  state.playbook.draft = state.playbook.data.text;
  return true;
}
window.addEventListener("beforeunload", (e) => { if (playbookDirty()) { e.preventDefault(); e.returnValue = ""; } });

function openPlaybook(slug) {
  history.pushState({ fromRun: true }, "", playbookHash(slug));
  showPlaybook(slug);
}

async function showPlaybook(slug) {
  state.view = "playbook";
  state.playbook = { slug, data: null, draft: "", mode: "read", message: null, error: null };
  render();
  window.scrollTo(0, 0);
  try {
    const data = await api(`/api/playbooks/${slug.split("/").map(encodeURIComponent).join("/")}`);
    Object.assign(state.playbook, { data, draft: data.text });
  } catch (e) {
    state.playbook.error = `Could not load playbook: ${e.message}`;
  }
  render();
}

function backToIncident() {
  if (!confirmLeavePlaybook()) return;
  state.playbook.draft = state.playbook.data?.text ?? "";
  if (history.state?.fromRun) history.back();  // popstate re-renders the incident page
  else { history.replaceState(null, "", `#${encodeURIComponent(state.selected)}/report`); route(); }
}

async function savePlaybook() {
  const pb = state.playbook;
  const btn = $("#pb-save");
  if (btn) btn.disabled = true;
  try {
    const res = await api(`/api/playbooks/${pb.slug.split("/").map(encodeURIComponent).join("/")}`, {
      method: "PUT",
      body: JSON.stringify({ text: pb.draft, base_hash: pb.data.hash, editor: reviewer(), note: $("#pb-note")?.value || "" }),
    });
    Object.assign(pb, { data: res.playbook, draft: res.playbook.text, mode: "read", error: null,
      message: res.saved ? { warnings: res.warnings, backup: res.backup } : { warnings: [], unchanged: true } });
    loadHealth();
  } catch (e) {
    pb.error = e.message;
  }
  render();
}

function renderPlaybookPage() {
  const pb = state.playbook;
  const alertId = esc(state.selected);
  const back = `<button class="back plain" id="pb-back">${ic("chevronLeft")}${alertId}</button>`;
  if (!pb.data) {
    $("#main").innerHTML = `<div class="content">${back}${pb.error ? `<div class="banner bad">${ic("warning")}<div>${esc(pb.error)}</div></div>` : `<div class="empty">${ic("book")}Loading playbook…</div>`}</div>`;
    $("#pb-back").addEventListener("click", backToIncident);
    return;
  }
  const d = pb.data;
  const editing = pb.mode === "edit";
  const dirty = pb.draft !== d.text;
  const usedHere = (state.run?.playbooks || []).some((p) => p.slug === pb.slug);
  const banners = [
    pb.error ? `<div class="banner bad">${ic("warning")}<div>${esc(pb.error)}</div></div>` : "",
    pb.message?.unchanged ? `<div class="banner info">${ic("checkCircle")}<div>No changes to save.</div></div>` : "",
    pb.message && !pb.message.unchanged ? `<div class="banner ok">${ic("checkCircle")}<div><b>Saved.</b> The previous version is kept at <span class="mono">${esc(pb.message.backup)}</span>. New investigations use this version.</div></div>` : "",
    ...(pb.message?.warnings || []).map((w) => `<div class="banner bad">${ic("warning")}<div>${esc(w)}</div></div>`),
  ].join("");
  const rules = d.step_rules.length ? `
    <div class="group-title">Human-owned steps</div>
    <div class="card"><table><tr><th>Step (quoted from the playbook)</th><th>Owner</th><th>Gate</th></tr>
      ${d.step_rules.map((r) => `<tr><td>${esc(r.match)}</td><td>${badge(r.owner === "human" ? "human" : "", r.owner)}</td><td>${esc(r.gate.replaceAll("_", " "))}</td></tr>`).join("")}</table></div>` : "";
  const hist = d.history.length ? d.history.map((h) => `<tr><td>${esc(new Date(h.saved_at).toLocaleString())}</td><td>${esc(h.editor)}</td><td>${esc(h.note || "—")}</td><td class="mono">${esc(h.previous_version)}</td></tr>`).join("") : "";

  $("#main").innerHTML = `
    <div class="content">
      ${back}
      <div class="card pb-head">
        <span class="row-tile tint-brown pb-tile">${ic("book")}</span>
        <div class="grow">
          <div class="title">${esc(d.title)}</div>
          <div class="facts">
            <span>Trigger <b>${esc(d.alert_type)}</b></span>
            <span class="mono">${esc(d.path)}</span>
            ${d.origin !== "official" ? badge("awaiting_human", "AI-drafted") : badge("", "Official")}
            ${usedHere ? badge("completed", `Used for ${alertId}`) : ""}
            ${d.history.length ? `<span>${ic("history")}${plural(d.history.length, "edit")}</span>` : ""}
          </div>
        </div>
        <div class="pb-actions">
          <div class="segmented" role="tablist">
            <button class="${editing ? "" : "active"}" data-pb-mode="read">${ic("eye")}Read</button>
            <button class="${editing ? "active" : ""}" data-pb-mode="edit">${ic("pencil")}Edit</button>
          </div>
        </div>
      </div>
      ${banners}
      ${editing ? `
        <div class="pb-split">
          <div class="pb-pane">
            <div class="pane-label"><span class="label">Markdown</span><span id="pb-dirty" ${dirty ? "" : "hidden"}>${badge("awaiting_human", "Unsaved changes")}</span></div>
            <textarea id="pb-editor" class="pb-editor" spellcheck="false">${esc(pb.draft)}</textarea>
          </div>
          <div class="pb-pane">
            <div class="pane-label"><span class="label">Preview</span></div>
            <article id="pb-preview" class="card markdown">${renderMarkdown(pb.draft)}</article>
          </div>
        </div>
        <div class="card pb-savebar">
          <input id="pb-note" placeholder="What changed? (optional)">
          <span class="muted small">Saving as <b>${esc(reviewer())}</b> · the current version is backed up first</span>
          <button class="secondary" id="pb-cancel">Cancel</button>
          <button id="pb-save" ${dirty ? "" : "disabled"}>${ic("save")}Save</button>
        </div>` : `<article class="card markdown">${renderMarkdown(d.text)}</article>`}
      ${rules}
      ${hist ? `<div class="group-title">Edit history</div><div class="card"><table><tr><th>Saved</th><th>By</th><th>Note</th><th>Previous version</th></tr>${hist}</table></div>` : ""}
    </div>`;

  $("#pb-back").addEventListener("click", backToIncident);
  document.querySelectorAll("[data-pb-mode]").forEach((b) => b.addEventListener("click", () => {
    if (b.dataset.pbMode === "read" && dirty && !window.confirm("Discard unsaved changes?")) return;
    if (b.dataset.pbMode === "read") pb.draft = d.text;
    pb.mode = b.dataset.pbMode;
    pb.message = null;
    pb.error = null;
    render();
  }));
  const editor = $("#pb-editor");
  if (editor) {
    editor.addEventListener("input", () => {
      pb.draft = editor.value;
      $("#pb-preview").innerHTML = renderMarkdown(pb.draft);
      $("#pb-save").disabled = pb.draft === d.text;
      $("#pb-dirty").hidden = pb.draft === d.text;
    });
    editor.addEventListener("keydown", (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "s") { e.preventDefault(); if (pb.draft !== d.text) savePlaybook(); }
    });
    $("#pb-save").addEventListener("click", savePlaybook);
    $("#pb-cancel").addEventListener("click", () => {
      if (pb.draft !== d.text && !window.confirm("Discard unsaved changes?")) return;
      pb.draft = d.text;
      pb.mode = "read";
      render();
    });
  }
}

// Logo: the organisation's file from web/brand/ when present, else the built-in shield.
const logo = { url: null, checked: false };
async function loadLogo() {
  try {
    const res = await fetch("/brand/logo", { method: "HEAD" });
    if (res.ok) logo.url = "/brand/logo";
  } catch {}
  logo.checked = true;
  fillLogos();
}
function fillLogos() {
  if (!logo.checked) return;
  document.querySelectorAll("[data-logo]").forEach((el) => {
    el.classList.toggle("has-logo", !!logo.url);
    el.innerHTML = logo.url ? `<img src="${logo.url}" alt="">` : ic("shield");
  });
}

// Static icons in index.html.
document.querySelectorAll("[data-icon]").forEach((el) => el.insertAdjacentHTML("afterbegin", ic(el.dataset.icon)));
loadHealth();
// Hash routes: #ALERT, #ALERT/<tab>, #ALERT/playbook/<slug>
async function route() {
  const [id, part, ...rest] = location.hash.slice(1).split("/").map(decodeURIComponent);
  if (!id || !state.alerts.some((a) => a.alert_id === id)) return renderHome();
  if (state.selected !== id) {
    state.selected = id;
    const alert = state.alerts.find((a) => a.alert_id === id);
    state.run = alert?.last_run ? await api(`/api/runs/${alert.last_run.run_id}`) : null;
    watchRun();
  }
  if (part === "playbook" && rest.length) return showPlaybook(rest.join("/"));
  state.view = "run";
  if (part) state.tab = part;
  render();
}
window.addEventListener("popstate", () => {
  if (state.view === "playbook" && !confirmLeavePlaybook()) {
    history.pushState(null, "", playbookHash(state.playbook.slug));
    return;
  }
  route();
});

loadLogo();
loadAlerts().then(route);
