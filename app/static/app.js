'use strict';
let token = '';
let session = 0;
let refreshRequest = 0;
let detailRequest = 0;
const el = id => document.getElementById(id);
function status(message) { el('status').textContent = message; }
async function api(path, method = 'GET', body) {
  if (!token) throw new Error('Zuerst mit einem API-Token verbinden.');
  const response = await fetch('/api/' + path, {method, headers: {Authorization: 'Bearer ' + token, 'Content-Type': 'application/json'}, ...(body ? {body: JSON.stringify(body)} : {})});
  if (!response.ok) throw new Error(`API ${response.status}: ${JSON.stringify((await response.json()).detail)}`);
  return response.json();
}
function list(id, rows, render) {
  el(id).replaceChildren();
  if (!rows.length) rows = [null];
  rows.forEach(row => { const item = document.createElement('li'); if (row) render(item, row); else item.textContent = 'Keine Einträge vorhanden.'; el(id).append(item); });
}
function clearWorkspace(message = 'Nicht geladen — keine aktuellen Daten.') {
  ['projects', 'evidence', 'tasks', 'storage', 'context-hits', 'results'].forEach(id => {
    const item = document.createElement('li'); item.textContent = message; el(id).replaceChildren(item);
  });
  const option = document.createElement('option'); option.value = ''; option.textContent = message;
  el('context-project').replaceChildren(option);
  el('cache-summary').textContent = 'Keine aktuellen Speicherwerte verfügbar.';
  el('stop').textContent = 'Unbekannt — Status nicht bestätigt.';
  el('runtime-mode').textContent = 'Instanzmodus nicht bestätigt.';
  detailRequest++; el('challenge-detail').replaceChildren();
  el('challenge-worker-state').textContent = 'Worker-Konfiguration nicht bestätigt.';
}
async function refresh() {
  const current = session;
  const request = ++refreshRequest;
  try {
    const [projects, evidence, tasks, stop, storage, runtime, results] = await Promise.all(['projects', 'evidence', 'tasks', 'control/stop', 'storage/health', 'runtime', 'results'].map(path => api(path)));
    if (current !== session || request !== refreshRequest) return;
    if (!['test', 'operational'].includes(runtime.mode)) throw new Error('Instanzmodus unbekannt; Daten nicht als Betrieb bestätigt.');
    list('projects', projects, (node, row) => { node.textContent = `${row.name} — ${row.description || 'Ohne Beschreibung'} · ${row.id}`; });
    list('evidence', evidence, (node, row) => { node.textContent = `${row.claim} · ${row.state} · gemeldete Confidence ${row.confidence}`; });
    list('tasks', tasks, (node, row) => { node.textContent = `${row.title} · ${row.action} `; const button = document.createElement('button'); button.textContent = 'Triage prüfen'; button.onclick = async () => { const selectedSession = session; try { const decision = await api(`tasks/${row.id}/triage`, 'POST'); if (selectedSession !== session) return; status(`${decision.state}: ${decision.reasons.join('; ')}`); } catch (error) { if (selectedSession === session) status(error.message); } }; node.append(button); });
    list('storage', storage.tiers, (node, row) => { node.textContent = row.available ? `${row.tier.toUpperCase()} (Dateisystempfad): ${row.used_percent}% belegt · ${Math.round(row.free_bytes / 1048576)} MiB frei` : `${row.tier.toUpperCase()}: ${row.status} — ${row.reason}`; });
    el('cache-summary').textContent = `Cache aktiv: ${storage.cache_active_bytes} Bytes · abgelaufen, zur Bereinigung: ${storage.cache_expired_bytes} Bytes · Archiv logisch: ${storage.archive_logical_bytes} Bytes (ohne Kopien/Index)`;
    const selected = el('context-project').value;
    el('context-project').replaceChildren();
    projects.forEach(project => { const option = document.createElement('option'); option.value = project.id; option.textContent = project.name; el('context-project').append(option); });
    if (projects.some(project => project.id === selected)) el('context-project').value = selected;
    el('stop').textContent = stop.active ? 'STOP AKTIV — Triage blockiert' : 'Kein Stop aktiv — keine Ausführung implementiert';
    el('runtime-mode').textContent = runtime.mode === 'test' ? 'TESTINSTANZ — Testeingaben sind keine Live-/Gerätenachweise.' : 'BETRIEBSINSTANZ — keine automatisch eingesetzten Beispieldaten. Produktionsfreigabe nicht validiert.';
    el('challenge-worker-state').textContent = `Challenge Worker: ${runtime.challenge_worker}`;
    detailRequest++; el('challenge-detail').replaceChildren();
    list('results', results, renderResult);
    status('Verbunden. Daten aus dem aktuellen Workspace geladen.');
  } catch (error) { if (current === session && request === refreshRequest) { clearWorkspace('Daten nicht verfügbar — kein Ersatz durch Beispieldaten.'); status(error.message); } }
}
el('login').onsubmit = event => { event.preventDefault(); session++; clearWorkspace(); token = el('token').value; el('token').value = ''; refresh(); };
el('logout').onclick = () => { session++; token = ''; clearWorkspace('Getrennt — keine aktuellen Daten.'); status('Getrennt.'); };
el('refresh').onclick = refresh;
el('project').onsubmit = async event => { event.preventDefault(); const current = session; try { const body = Object.fromEntries(new FormData(event.target)); await api('projects', 'POST', body); if (current !== session) return; event.target.reset(); await refresh(); } catch (error) { if (current === session) status(error.message); } };

el('context-search').onsubmit = async event => {
  event.preventDefault();
  const current = session;
  el('context-hits').replaceChildren();
  try {
    const hits = await api('context/query', 'POST', Object.fromEntries(new FormData(event.target)));
    if (current !== session) return;
    list('context-hits', hits, (node, hit) => {
      node.textContent = `${hit.category} · ${hit.logical_path} · ${hit.location} · Zeichen ${hit.start_char}–${hit.end_char} · Evidence: ${hit.evidence_state} · Decision: ${hit.decision_status || 'kein Decision-Pass'} · Result: ${hit.decision_result_id || '—'} · SHA-256 ${hit.sha256} · ${hit.timestamp}
${hit.text}`;
    });
    status(`${hits.length} Texttreffer. Keine automatische Aktionsfreigabe.`);
  } catch (error) { if (current === session) status(error.message); }
};

function detailLine(text) {
  const line = document.createElement('p'); line.textContent = text; el('challenge-detail').append(line);
}
async function showWhy(result, sources = false) {
  const current = session;
  const request = ++detailRequest;
  el('challenge-detail').replaceChildren();
  try {
    const data = await api(`results/${result.id}/why`);
    if (current !== session || request !== detailRequest) return;
    detailLine(`Primärtext — nicht semantisch validiert: ${data.result.summary}`);
    detailLine(`Abgerufener Entscheidungssnapshot für Result ${data.decision.result_id}: ${data.decision.validation_status} / ${data.decision.state}. Report für dieses Ergebnis aktuell: ${data.current ? 'JA' : 'NEIN — keine Freigabe aus diesem Bericht'}`);
    detailLine(`Challenge-Job: ${data.latest_job?.state || 'NOT RUN'} · ${data.decision.reasons.join('; ')}`);
    if (data.report) {
      detailLine(`${data.current ? 'Gegenprüfung' : 'Historischer Bericht — NICHT zur Freigabe verwenden'}: ${data.report.analysis.verdict}; Scope: ${data.report.analysis.scope}`);
      data.report.analysis.findings.forEach(f => detailLine(`${f.check} / ${f.severity}: ${f.message} · Evidence: ${f.evidence_ids.join(', ') || 'keine Referenz'} · Nächste Validierung: ${f.next_validation}`));
      data.report.analysis.alternatives.forEach(a => detailLine(`Belegter Gegenkandidat nur für diese Eigenschaft: ${a.subject} / ${a.variant} / ${a.revision} · ${a.attribute}=${a.value} ${a.unit} · Evidence ${a.evidence_id}`));
    }
    if (sources) {
      const ids = [...new Set([...result.claims.flatMap(c => c.evidence_ids), ...result.alternatives.flatMap(a => a.evidence_ids), ...(data.report?.analysis.findings.flatMap(f => f.evidence_ids) || []), ...(data.report?.analysis.alternatives.map(a => a.evidence_id) || [])])];
      detailLine(`Quellen: erste ${Math.min(ids.length, 30)} von ${ids.length} Referenzen; weitere über die API.`);
      const rows = await Promise.all(ids.slice(0, 30).map(id => api(`evidence/${id}`)));
      if (current !== session || request !== detailRequest) return;
      rows.forEach(e => detailLine(`Evidence ${e.id} · ${e.state} · ${e.source_url} · beobachtet ${e.observed_at} · SHA-256 ${e.sha256} · eingereichter Originaltext: ${e.content}`));
    }
  } catch (error) { if (current === session && request === detailRequest) { el('challenge-detail').replaceChildren(); detailLine(`Gegenprüfung nicht verfügbar: ${error.message}`); } }
}
function renderResult(node, result) {
  node.textContent = `Primärpaket ${result.id} · ${result.kind} · ${result.primary_worker} (angegebene Herkunft). Status über „Warum?“ aktuell prüfen. `;
  const why = document.createElement('button'); why.textContent = 'Warum?'; why.onclick = () => showWhy(result);
  const sources = document.createElement('button'); sources.textContent = 'Quellen'; sources.onclick = () => showWhy(result, true);
  const challenge = document.createElement('button'); challenge.textContent = 'Herausfordern';
  const form = document.createElement('form'); form.hidden = true;
  const label = document.createElement('label'); label.textContent = 'Konkreter Grund der Gegenprüfung (bisherige Freigabe wird entwertet)';
  const reason = document.createElement('input'); reason.required = true; reason.maxLength = 2000; label.append(reason);
  const submit = document.createElement('button'); submit.type = 'submit'; submit.textContent = 'Neue Challenge anfordern'; form.append(label, submit);
  challenge.onclick = () => { form.hidden = !form.hidden; if (!form.hidden) reason.focus(); };
  form.onsubmit = async event => {
    event.preventDefault(); const current = session; submit.disabled = true;
    try {
      const job = await api(`results/${result.id}/challenge`, 'POST', {reason: reason.value});
      if (current !== session) return;
      status(`Challenge ${job.id} angefordert: ${job.state}. Noch kein Gegenprüfungsresultat.`);
      form.hidden = true; await showWhy(result);
    } catch (error) { if (current === session) status(error.message); }
    finally { submit.disabled = false; }
  };
  node.append(why, challenge, sources, form);
}
