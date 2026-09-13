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
    const [projects, evidence, tasks, stop] = await Promise.all(['projects', 'evidence', 'tasks', 'control/stop'].map(path => api(path)));
    if (current !== session) return;
    list('projects', projects, (node, row) => { node.textContent = `${row.name} — ${row.description || 'Ohne Beschreibung'} · ${row.id}`; });
    list('evidence', evidence, (node, row) => { node.textContent = `${row.claim} · ${row.state} · gemeldete Confidence ${row.confidence}`; });
    list('tasks', tasks, (node, row) => { node.textContent = `${row.title} · ${row.action} `; const button = document.createElement('button'); button.textContent = 'Triage prüfen'; button.onclick = async () => { try { const decision = await api(`tasks/${row.id}/triage`, 'POST'); status(`${decision.state}: ${decision.reasons.join('; ')}`); } catch (error) { status(error.message); } }; node.append(button); });
    el('stop').textContent = stop.active ? 'STOP AKTIV — Triage blockiert' : 'Kein Stop aktiv — keine Ausführung implementiert';
    status('Verbunden. Daten aus dem aktuellen Workspace geladen.');
  } catch (error) { if (current === session) status(error.message); }
}
el('login').onsubmit = event => { event.preventDefault(); session++; ['projects', 'evidence', 'tasks'].forEach(id => el(id).replaceChildren()); token = el('token').value; el('token').value = ''; refresh(); };
el('logout').onclick = () => { session++; token = ''; ['projects', 'evidence', 'tasks'].forEach(id => { el(id).replaceChildren(); }); el('stop').textContent = 'Unbekannt — zuerst verbinden.'; status('Getrennt.'); };
el('refresh').onclick = refresh;
el('project').onsubmit = async event => { event.preventDefault(); try { const body = Object.fromEntries(new FormData(event.target)); await api('projects', 'POST', body); event.target.reset(); await refresh(); } catch (error) { status(error.message); } };
