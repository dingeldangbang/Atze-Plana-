'use strict';
let token = '';
let session = 0;
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
async function refresh() {
  const current = session;
  try {
    const [projects, evidence, tasks, stop, storage] = await Promise.all(['projects', 'evidence', 'tasks', 'control/stop', 'storage/health'].map(path => api(path)));
    if (current !== session) return;
    list('projects', projects, (node, row) => { node.textContent = `${row.name} — ${row.description || 'Ohne Beschreibung'} · ${row.id}`; });
    list('evidence', evidence, (node, row) => { node.textContent = `${row.claim} · ${row.state} · gemeldete Confidence ${row.confidence}`; });
    list('tasks', tasks, (node, row) => { node.textContent = `${row.title} · ${row.action} `; const button = document.createElement('button'); button.textContent = 'Triage prüfen'; button.onclick = async () => { try { const decision = await api(`tasks/${row.id}/triage`, 'POST'); status(`${decision.state}: ${decision.reasons.join('; ')}`); } catch (error) { status(error.message); } }; node.append(button); });
    list('storage', storage.tiers, (node, row) => { node.textContent = row.available ? `${row.tier.toUpperCase()}: ${row.used_percent}% belegt · ${Math.round(row.free_bytes / 1048576)} MiB frei` : `${row.tier.toUpperCase()}: nicht konfiguriert / nicht verfügbar`; });
    el('cache-summary').textContent = `Cache aktiv: ${storage.cache_active_bytes} Bytes · abgelaufen, zur Bereinigung: ${storage.cache_expired_bytes} Bytes · Archiv logisch: ${storage.archive_logical_bytes} Bytes (ohne Kopien/Index)`;
    const selected = el('context-project').value;
    el('context-project').replaceChildren();
    projects.forEach(project => { const option = document.createElement('option'); option.value = project.id; option.textContent = project.name; el('context-project').append(option); });
    if (projects.some(project => project.id === selected)) el('context-project').value = selected;
    el('stop').textContent = stop.active ? 'STOP AKTIV — Triage blockiert' : 'Kein Stop aktiv — keine Ausführung implementiert';
    status('Verbunden. Daten aus dem aktuellen Workspace geladen.');
  } catch (error) { if (current === session) status(error.message); }
}
el('login').onsubmit = event => { event.preventDefault(); session++; el('cache-summary').textContent = 'Keine Messwerte geladen.'; ['projects', 'evidence', 'tasks', 'storage', 'context-hits', 'context-project'].forEach(id => el(id).replaceChildren()); token = el('token').value; el('token').value = ''; refresh(); };
el('logout').onclick = () => { session++; token = ''; el('cache-summary').textContent = 'Keine Messwerte geladen.'; ['projects', 'evidence', 'tasks', 'storage', 'context-hits', 'context-project'].forEach(id => { el(id).replaceChildren(); }); el('stop').textContent = 'Unbekannt — zuerst verbinden.'; status('Getrennt.'); };
el('refresh').onclick = refresh;
el('project').onsubmit = async event => { event.preventDefault(); try { const body = Object.fromEntries(new FormData(event.target)); await api('projects', 'POST', body); event.target.reset(); await refresh(); } catch (error) { status(error.message); } };

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
