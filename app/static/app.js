'use strict';
let token = '';
let session = 0;
let refreshRequest = 0;
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
  ['projects', 'evidence', 'tasks', 'storage', 'context-hits'].forEach(id => {
    const item = document.createElement('li'); item.textContent = message; el(id).replaceChildren(item);
  });
  const option = document.createElement('option'); option.value = ''; option.textContent = message;
  el('context-project').replaceChildren(option);
  el('cache-summary').textContent = 'Keine aktuellen Speicherwerte verfügbar.';
  el('stop').textContent = 'Unbekannt — Status nicht bestätigt.';
  el('runtime-mode').textContent = 'Instanzmodus nicht bestätigt.';
}
async function refresh() {
  const current = session;
  const request = ++refreshRequest;
  try {
    const [projects, evidence, tasks, stop, storage, runtime] = await Promise.all(['projects', 'evidence', 'tasks', 'control/stop', 'storage/health', 'runtime'].map(path => api(path)));
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
      node.textContent = `${hit.category} · ${hit.logical_path} · ${hit.location} · Zeichen ${hit.start_char}–${hit.end_char} · Evidence: ${hit.evidence_state} · SHA-256 ${hit.sha256} · ${hit.timestamp}
${hit.text}`;
    });
    status(`${hits.length} Texttreffer. Keine automatische Aktionsfreigabe.`);
  } catch (error) { if (current === session) status(error.message); }
};
