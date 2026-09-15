'use strict';
let token = '';
let session = 0;
let refreshRequest = 0;
let detailRequest = 0;
let planRequest = 0;
let planSources = [];
let planTasks = [];
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
  ['projects', 'evidence', 'tasks', 'storage', 'context-hits', 'results', 'ai-providers', 'plans', 'monitor-list', 'trend-results', 'integrations'].forEach(id => {
    const item = document.createElement('li'); item.textContent = message; el(id).replaceChildren(item);
  });
  const option = document.createElement('option'); option.value = ''; option.textContent = message;
  el('context-project').replaceChildren(option);
  ['trend-sensor', 'sensor-device', 'agent-model'].forEach(id => {
    const empty = document.createElement('option'); empty.value = ''; empty.textContent = message; el(id).replaceChildren(empty);
  });
  el('trend-run').disabled = true; el('agent-add-submit').disabled = true;
  planRequest++; planSources = []; planTasks = []; resetPlanEditor();
  el('plan-task').replaceChildren(); el('plan-resources').replaceChildren(); el('plan-detail').replaceChildren();
  el('cache-summary').textContent = 'Keine aktuellen Speicherwerte verfügbar.';
  el('ai-policy-state').textContent = 'KI-Policy nicht bestätigt.';
  el('stop').textContent = 'Unbekannt — Status nicht bestätigt.';
  el('runtime-mode').textContent = 'Instanzmodus nicht bestätigt.';
  detailRequest++; el('challenge-detail').replaceChildren();
  el('challenge-worker-state').textContent = 'Worker-Konfiguration nicht bestätigt.';
}
async function refresh() {
  const current = session;
  const request = ++refreshRequest;
  status('Lade aktuelle Workspace-Daten…');
  try {
    const [projects, evidence, tasks, stop, storage, runtime, results, ai, plans, archives, memories, monitoring, integrationRegistry, devices, models] = await Promise.all(['projects', 'evidence', 'tasks', 'control/stop', 'storage/health', 'runtime', 'results', 'ai/status', 'plans', 'archive', 'memory', 'monitoring/overview', 'integrations', 'telemetry/devices', 'ai/models'].map(path => api(path)));
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
    planRequest++; el('plan-detail').replaceChildren();
    planTasks = tasks; planSources = [...evidence.map(v => ({kind:'evidence', ...v})), ...archives.map(v => ({kind:'archive', ...v})), ...memories.map(v => ({kind:'memory', ...v}))];
    const selectedTask = el('plan-task').value; el('plan-task').replaceChildren();
    tasks.forEach(task => { const option = document.createElement('option'); option.value = task.id; option.textContent = `${task.title} · ${task.id}`; el('plan-task').append(option); });
    if (tasks.some(t => t.id === selectedTask)) el('plan-task').value = selectedTask;
    resetPlanEditor(); list('plans', plans, renderPlan);
    el('ai-policy-state').textContent = `KI Privacy Lock: ${ai.policy.privacy_lock ? 'AN' : 'AUS'} · Local-only: ${ai.policy.local_only ? 'JA' : 'NEIN'} · External AI: ${ai.policy.external_ai ? 'ALLOW (weitere Gates erforderlich)' : 'DENY'} · Modellvalidierung: ${ai.model_inference}`;
    list('ai-providers', ai.providers, (node, row) => { node.textContent = `${row.id} · ${row.mode} · Region (konfiguriert): ${row.region} · ${row.status}`; });
    renderMonitoring(monitoring);
    renderIntegrations(integrationRegistry, devices, models);
    status('Verbunden. Daten aus dem aktuellen Workspace geladen.');
  } catch (error) { if (current === session && request === refreshRequest) { clearWorkspace('Daten nicht verfügbar — kein Ersatz durch Beispieldaten.'); status(error.message); } }
}
el('login').onsubmit = event => { event.preventDefault(); session++; clearWorkspace(); token = el('token').value; el('token').value = ''; refresh(); };
el('logout').onclick = () => { session++; token = ''; el('token').value = ''; clearWorkspace('Getrennt — keine aktuellen Daten.'); status('Getrennt.'); };
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

el('ai-lock').onclick = async () => {
  const current = session;
  try {
    await api('ai/policy', 'POST', {});
    if (current !== session) return;
    await refresh();
    if (current === session) status('KI gesperrt: Local-only, External DENY, alle Allowlists geleert. Bereits laufende Übertragung nicht rückrufbar.');
  } catch (error) { if (current === session) status(error.message); }
};

function resetPlanEditor() {
  el('plan-editor').reset(); el('plan-id').value = ''; el('plan-version-id').value = ''; el('plan-task').disabled = false;
  fillPlanSources();
}
function fillPlanSources(selected = []) {
  const task = planTasks.find(t => t.id === el('plan-task').value);
  el('plan-resources').replaceChildren();
  if (!task) return;
  planSources.filter(s => s.project_id === task.project_id && (s.kind !== 'memory' || !s.task_id || s.task_id === task.id)).forEach(source => {
    const option = document.createElement('option'); option.value = JSON.stringify({kind:source.kind,id:source.id});
    option.textContent = `${source.kind} · ${source.logical_path || source.claim || source.category} · ${source.id}`;
    option.selected = selected.some(s => s.kind === source.kind && s.id === source.id); el('plan-resources').append(option);
  });
}
function planLine(text) { const node = document.createElement('p'); node.textContent = text; el('plan-detail').append(node); }
async function showPlan(plan, edit = false) {
  const current = session, request = ++planRequest; el('plan-detail').replaceChildren();
  try {
    const [versions, state] = await Promise.all([api(`plans/${plan.id}/versions?limit=1`), api(`plans/${plan.id}/status`)]);
    if (current !== session || request !== planRequest) return;
    const version = versions[0];
    planLine(`${state.state}: ${state.reason} · PLAN ${plan.id} · Version ${version.version} · ${version.title}`);
    planLine(`Manifest SHA-256 ${version.manifest_hash} · Lock ${state.lock_id || 'keiner'} · Keine Aktionsberechtigung.`);
    version.manifest.resources.forEach(r => planLine(`${r.kind} ${r.id} · Beziehung (angegeben): ${r.relationship} · ${r.size_bytes} Bytes · SHA-256 ${r.sha256} · Byteintegrität bei Erfassung: ${r.content_integrity} · Wahrheitsstatus: ${r.truth_status} · Review: ${r.review_state || 'kein Review'} · Quelle: ${r.source_url || r.logical_path || 'Memory-Referenz'}`));
    if (edit && version.resources.some(r => !planSources.some(s => s.kind === r.kind && s.id === r.id))) throw new Error('Nicht alle gewählten Quellen sind in den ersten 100 Einträgen verfügbar. Version über die API bearbeiten; keine Quelle wird still entfernt.');
    if (edit && version.resources.some(r => r.relationship !== 'input')) throw new Error('Beziehungen außer input bitte über die API bearbeiten; Oberfläche überschreibt sie nicht.');
    if (edit) {
      el('plan-id').value = plan.id; el('plan-version-id').value = version.id;
      el('plan-task').value = plan.task_id; el('plan-task').disabled = true;
      el('plan-title').value = version.title; el('plan-type').value = version.context_type;
      fillPlanSources(version.resources);
    }
    const form = document.createElement('form'); const label = document.createElement('label'); label.textContent = 'Expliziter Prüf-/Widerrufsgrund (Reviewer)';
    const reason = document.createElement('input'); reason.required = true; reason.maxLength = 2000; label.append(reason);
    const lock = document.createElement('button'); lock.textContent = 'Diese Version neu sperren'; lock.type = 'submit'; form.append(label, lock);
    form.onsubmit = async event => {
      event.preventDefault(); lock.disabled = true;
      try { await api(`plans/${plan.id}/locks`, 'POST', {version_id:version.id,manifest_hash:version.manifest_hash,reason:reason.value}); if (current === session) await showPlan(plan); }
      catch (error) { if (current === session) status(error.message); }
      finally { lock.disabled = false; }
    };
    if (state.lock_id && state.state !== 'REVOKED') {
      const revoke = document.createElement('button'); revoke.type = 'button'; revoke.textContent = 'Context Lock widerrufen';
      revoke.onclick = async () => {
        if (!form.reportValidity()) return; revoke.disabled = true;
        try { await api(`plan-locks/${state.lock_id}/revoke`, 'POST', {reason:reason.value}); if (current === session) await showPlan(plan); }
        catch (error) { if (current === session) status(error.message); }
        finally { revoke.disabled = false; }
      }; form.append(revoke);
    }
    el('plan-detail').append(form);
  } catch (error) { if (current === session && request === planRequest) { el('plan-detail').replaceChildren(); planLine(`PLAN nicht als aktuell bestätigt: ${error.message}`); } }
}
function renderPlan(node, plan) {
  node.textContent = `PLAN ${plan.id} · Task ${plan.task_id} `;
  const details = document.createElement('button'); details.textContent = 'Kontext & Lock prüfen'; details.onclick = () => showPlan(plan);
  const edit = document.createElement('button'); edit.textContent = 'Neue Version vorbereiten'; edit.onclick = () => showPlan(plan, true);
  node.append(details, edit);
}
el('plan-reset').onclick = resetPlanEditor;
el('plan-task').onchange = () => fillPlanSources();
el('plan-editor').onsubmit = async event => {
  event.preventDefault(); const current = session;
  try {
    const resources = [...el('plan-resources').selectedOptions].map(o => JSON.parse(o.value));
    if (!resources.length || resources.length > 16) throw new Error('1 bis 16 vorhandene Quellen auswählen.');
    const body = {title:el('plan-title').value,context_type:el('plan-type').value,resources};
    const plan = el('plan-id').value;
    if (plan) await api(`plans/${plan}/versions`, 'POST', {...body,expected_version_id:el('plan-version-id').value});
    else await api('plans', 'POST', {...body,task_id:el('plan-task').value});
    if (current !== session) return;
    resetPlanEditor(); await refresh();
  } catch (error) { if (current === session) status(error.message); }
};

function renderMonitoring(monitoring) {
  const c = monitoring.counts, i = monitoring.integrations;
  list('monitor-list', [
    `Projekte ${c.projects} · Aufgaben ${c.tasks} · Evidenz ${c.evidence} · Resultate ${c.results} · Not-Stop ${monitoring.stop_active ? 'AKTIV' : 'inaktiv'}`,
    `Telemetrie-Geräte aktiv ${c.telemetry_devices.active} / deaktiviert ${c.telemetry_devices.deactivated} · Sensoren aktiv ${c.telemetry_sensors.active} / deaktiviert ${c.telemetry_sensors.deactivated} · Batches ${c.telemetry_batches} · Samples ${c.telemetry_samples} (davon suspect laut Device: ${c.telemetry_suspect_samples}, außerhalb deklarierter Range: ${c.telemetry_flagged_out_of_range})`,
    `Ressourcen aktiv ${c.resources.active} / deaktiviert ${c.resources.deactivated} · gespeicherte Versionsbytes ${c.resource_versions_stored_bytes} · Agenten aktiv ${c.agents.active} / deaktiviert ${c.agents.deactivated}`,
    `Agent-Runs: Consent ausstehend ${c.agent_runs.awaiting_consent} · DRAFT_UNCHALLENGED ${c.agent_runs.draft_unchallenged} · BLOCKED ${c.agent_runs.blocked} · UNAVAILABLE ${c.agent_runs.unavailable}`,
    `KI-Provider konfiguriert ${i.ai_providers.length} (konfiguriert ≠ validiert) · Bright-Data-MCP ${i.brightdata_mcp.configured ? 'CONFIGURED (Discovery/Tools-Call möglich; Live-Validierung separat)' : 'NOT_CONFIGURED'} · Telemetrie-Ingest ${i.telemetry_ingest.configured ? 'CONFIGURED (HTTP/HTTPS)' : 'NOT_CONFIGURED (Ingest verweigert)'}`,
    `Speicher: ${monitoring.storage.tiers.map(t => `${t.tier}=${t.status}`).join(' · ')} · Cache aktiv ${monitoring.storage.cache_active_bytes} B / abgelaufen ${monitoring.storage.cache_expired_bytes} B · Archiv logisch ${monitoring.storage.archive_logical_bytes} B`,
  ], (node, row) => { node.textContent = row; });
}

function fillSelect(id, rows, render) {
  const keep = el(id).value;
  el(id).replaceChildren();
  rows.forEach(row => { const option = document.createElement('option'); option.value = row.id; option.textContent = render(row); el(id).append(option); });
  if (rows.some(row => row.id === keep)) el(id).value = keep;
  return rows.length;
}
function renderIntegrations(registry, devices, models) {
  const activeDevices = devices.filter(d => d.state === 'active');
  if (!fillSelect('sensor-device', activeDevices, d => `${d.name} · ${d.id}`)) { const empty = document.createElement('option'); empty.value = ''; empty.textContent = 'Keine aktiven Geräte'; el('sensor-device').append(empty); }
  const sensors = registry.manageable.filter(b => b.binding === 'telemetry_device').flatMap(d => d.sensors || []);
  const activeSensors = sensors.filter(s => s.state === 'active');
  if (!fillSelect('trend-sensor', activeSensors, s => `${s.name} (${s.kind}) · ${s.id}`)) { const empty = document.createElement('option'); empty.value = ''; empty.textContent = 'Keine aktiven Sensoren'; el('trend-sensor').append(empty); }
  el('trend-run').disabled = activeSensors.length === 0;
  if (!fillSelect('agent-model', models, m => `${m.model} · ${m.provider_id} · ${m.capabilities.join('/')}`)) { const empty = document.createElement('option'); empty.value = ''; empty.textContent = 'Kein Modell registriert (AI-Status/Modelle prüfen)'; el('agent-model').append(empty); }
  el('agent-add-submit').disabled = models.length === 0;
  const rows = [...registry.manageable, ...registry.environment_bound];
  list('integrations', rows, renderBinding);
}
function renderBinding(node, binding) {
  if (binding.binding === 'ai_provider') {
    node.textContent = `[ai_provider] ${binding.id} · ${binding.state} · Server-Umgebung (Umgebungsvariable) · keine Verwaltung zur Laufzeit`;
    return;
  }
  if (binding.binding === 'brightdata_mcp') {
    node.textContent = `[brightdata_mcp] Bright-Data-MCP · ${binding.state} · ${binding.management}`;
    return;
  }
  if (binding.binding === 'telemetry_device_fleet') {
    node.textContent = `[telemetry_token] Ingest-Token · ${binding.state} · ${binding.management}`;
    return;
  }
  node.textContent = `[${binding.binding}] ${binding.name}${binding.kind ? ` (${binding.kind})` : ''}${binding.purpose ? ` (${binding.purpose})` : ''} · ${binding.state}${binding.version ? ` · v${binding.version}` : ''} · ${binding.id} `;
  if (binding.state === 'active') {
    const remove = document.createElement('button'); remove.textContent = 'Entfernen (−)';
    remove.onclick = () => confirmRemove(node, binding);
    node.append(remove);
  }
  if (binding.sensors && binding.sensors.length) {
    const nested = document.createElement('ul');
    binding.sensors.forEach(sensor => {
      const item = document.createElement('li');
      item.textContent = `[telemetry_sensor] ${sensor.name} (${sensor.kind})${sensor.unit ? ` [${sensor.unit}]` : ''} · ${sensor.state} · ${sensor.id} `;
      if (sensor.state === 'active') {
        const remove = document.createElement('button'); remove.textContent = 'Entfernen (−)';
        remove.onclick = () => confirmRemove(item, sensor);
        item.append(remove);
      }
      nested.append(item);
    });
    node.append(nested);
  }
}
function confirmRemove(node, binding) {
  if (node.querySelector('form')) return;
  const current = session;
  const form = document.createElement('form');
  const label = document.createElement('label'); label.textContent = `"${binding.name || binding.binding}" wirklich deaktivieren? Begründung (Pflicht):`;
  const reason = document.createElement('input'); reason.required = true; reason.maxLength = 2000; label.append(reason);
  const yes = document.createElement('button'); yes.textContent = 'Bestätigt deaktivieren (−)';
  const no = document.createElement('button'); no.type = 'button'; no.textContent = 'Abbrechen';
  form.append(label, yes, no); node.append(form); reason.focus();
  no.onclick = () => form.remove();
  form.onsubmit = async event => {
    event.preventDefault(); yes.disabled = true;
    try {
      await api(binding.actions.remove.route.split(' ')[1].replace(/^\/api\//, ''), 'POST', {confirm: true, reason: reason.value});
      if (current !== session) return;
      status(`Anbindung [${binding.binding}] deaktiviert (−). Daten und Historie bleiben vollständig erhalten; kein Lösch-Endpunkt existiert.`);
      await refresh();
    } catch (error) { yes.disabled = false; if (current === session) status(error.message); }
  };
}

el('device-add').onsubmit = async event => {
  event.preventDefault(); const current = session;
  try {
    const data = Object.fromEntries(new FormData(event.target));
    const device = await api('telemetry/devices', 'POST', {name: data.name, description: data.description});
    if (current !== session) return;
    event.target.reset();
    status(`Telemetrie-Gerät registriert (+): ${device.id}. Deklarative Identität, keine Hardwareverbindung hergestellt.`);
    await refresh();
  } catch (error) { if (current === session) status(error.message); }
};
el('sensor-add').onsubmit = async event => {
  event.preventDefault(); const current = session;
  try {
    const data = Object.fromEntries(new FormData(event.target));
    const body = {name: data.name, kind: data.kind};
    if (data.unit) body.unit = data.unit;
    if (data.minimum !== '' && data.maximum !== '') body.declared_range = {minimum: Number(data.minimum), maximum: Number(data.maximum)};
    else if (data.minimum !== '' || data.maximum !== '') throw new Error('Deklarierte Range benötigt beide Grenzen (Minimum < Maximum) oder keine.');
    await api(`telemetry/devices/${data.device_id}/sensors`, 'POST', body);
    if (current !== session) return;
    event.target.reset();
    status('Sensor deklariert (+). declared_range ist eine Owner-Angabe, keine Kalibrierung.');
    await refresh();
  } catch (error) { if (current === session) status(error.message); }
};
el('resource-add').onsubmit = async event => {
  event.preventDefault(); const current = session;
  const file = el('resource-file').files[0];
  try {
    if (!file) throw new Error('Keine Datei ausgewählt.');
    if (file.size > 4 * 1024 * 1024) throw new Error('Datei überschreitet die 4-MiB-Grenze eines einzelnen Uploads.');
    const bytes = new Uint8Array(await file.arrayBuffer());
    let binary = ''; for (let i = 0; i < bytes.length; i += 32768) binary += String.fromCharCode(...bytes.subarray(i, i + 32768));
    const data = Object.fromEntries(new FormData(event.target));
    const resource = await api('resources', 'POST', {name: data.name, kind: data.kind, source: data.source, description: `Upload über die Oberfläche · Datei ${file.name} · ${file.type || 'Typ unbekannt'}`, content_base64: btoa(binary)});
    if (current !== session) return;
    event.target.reset();
    status(`Ressource hochgeladen (+): ${resource.id} · ${resource.size_bytes} Bytes · Kein Virenscan durchgeführt (nicht implementiert, Betreiberverantwortung).`);
    await refresh();
  } catch (error) { if (current === session) status(error.message); }
};
el('agent-add').onsubmit = async event => {
  event.preventDefault(); const current = session;
  try {
    const data = Object.fromEntries(new FormData(event.target));
    const body = {name: data.name, model_id: data.model_id, purpose: data.purpose, instruction: data.instruction, description: 'Über die Oberfläche deklariert'};
    const tools = data.tools.split(',').map(t => t.trim()).filter(Boolean);
    if (tools.length) body.allowed_tools = tools;
    const agent = await api('agents', 'POST', body);
    if (current !== session) return;
    event.target.reset();
    status(`Agent deklariert (+): ${agent.id}. Runs erfordern separate Reviewer-Freigabe je Ausführung; keine autonome Tool-Ausführung.`);
    await refresh();
  } catch (error) { if (current === session) status(error.message); }
};
el('trend-form').onsubmit = async event => {
  event.preventDefault(); const current = session;
  try {
    const data = Object.fromEntries(new FormData(event.target));
    const body = {sensor_id: data.sensor_id};
    if (data.session) body.session = data.session;
    const report = await api('telemetry/trends', 'POST', body);
    if (current !== session) return;
    list('trend-results', [
      `Sensor ${report.sensor_id} · Samples ${report.sample_count}${report.session ? ` · Session ${report.session}` : ''} · ${report.summary_status} · CALCULATED aus eingereichten Samples, keine Prognose, keine Aktionsfreigabe`,
      ...report.checks.map(c => `${c.type}: ${c.status} · ${c.statistic} = ${c.value === null ? '—' : c.value} · Schwelle ${c.threshold}${c.failed_criteria.length ? ` · nicht erfüllt: ${c.failed_criteria.join('; ')}` : ''}`),
    ], (node, row) => { node.textContent = row; });
    status('Trend-Analyse abgeschlossen (Query ohne Nebenwirkungen).');
  } catch (error) { if (current === session) status(error.message); }
};
