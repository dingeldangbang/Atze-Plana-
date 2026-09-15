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
  ['projects', 'evidence', 'tasks', 'storage', 'context-hits', 'results', 'ai-providers', 'plans', 'monitor-list', 'trend-results', 'integrations', 'structures', 'structure-routes'].forEach(id => {
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
  structureReset(message);
}
async function refresh() {
  const current = session;
  const request = ++refreshRequest;
  status('Lade aktuelle Workspace-Daten…');
  try {
    const [projects, evidence, tasks, stop, storage, runtime, results, ai, plans, archives, memories, monitoring, integrationRegistry, devices, models, structures] = await Promise.all(['projects', 'evidence', 'tasks', 'control/stop', 'storage/health', 'runtime', 'results', 'ai/status', 'plans', 'archive', 'memory', 'monitoring/overview', 'integrations', 'telemetry/devices', 'ai/models', 'structures'].map(path => api(path)));
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
    list('structures', structures, (node, row) => { node.textContent = `${row.name} · ${row.state === 'active' ? 'aktiv' : 'deaktiviert'} · Version ${row.version} · ${row.id}`; });
    const structureKeep = structurePendingSelect || el('structure-select').value;
    structurePendingSelect = '';
    el('structure-select').replaceChildren();
    const structureEmpty = document.createElement('option'); structureEmpty.value = ''; structureEmpty.textContent = structures.length ? 'Struktur auswählen' : 'Keine Struktur vorhanden';
    el('structure-select').append(structureEmpty);
    structures.forEach(structure => { const option = document.createElement('option'); option.value = structure.id; option.textContent = `${structure.name} · v${structure.version} · ${structure.state}`; el('structure-select').append(option); });
    if (structures.some(structure => structure.id === structureKeep)) el('structure-select').value = structureKeep;
    if (el('structure-select').value) loadStructure(el('structure-select').value); else structureReset('Keine Struktur ausgewählt.');
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
    if (current === session) status('KI-Richtlinie auf lokal gesetzt: Local-only, External DENY, alle Allowlists geleert. Bereits laufende Übertragung nicht rückrufbar.');
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
    `KI-Provider konfiguriert ${i.ai_providers.length} (konfiguriert ≠ validiert) · Bright-Data-MCP ${i.brightdata_mcp.configured ? 'CONFIGURED (Discovery/Tools-Call möglich; Live-Validierung separat)' : 'NOT_CONFIGURED'} · Telemetrie-Ingest ${i.telemetry_ingest.configured ? 'CONFIGURED (HTTP/HTTPS)' : 'NOT_CONFIGURED (aktiviert sich mit dem Token)'}`,
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

/* Struktur-Builder (AXM v0.1) — lokale Staging-Entwürfe, versionierte Commits, CALCULATED-Generierung ohne Nebeneffekte. */
const SVG_NS = 'http://www.w3.org/2000/svg';
const NODE_W = 180, NODE_H = 64;
let structureSelected = '';
let structurePendingSelect = '';
let structureInfo = null;
let structureVersion = null;
let structureWorking = null;
let structurePositions = new Map();
let structureSelectedNode = null;
let structureRequest = 0;
let structureSuppressClick = false;

function svgElement(tag, attributes) {
  const node = document.createElementNS(SVG_NS, tag);
  Object.entries(attributes).forEach(([key, value]) => node.setAttribute(key, value));
  return node;
}
function svgPoint(svg, clientX, clientY) {
  const point = svg.createSVGPoint(); point.x = clientX; point.y = clientY;
  return point.matrixTransform(svg.getScreenCTM().inverse());
}
function structureHint(text) {
  const hint = document.createElement('p'); hint.className = 'muted'; hint.textContent = text;
  el('structure-inspector').replaceChildren(hint);
}
function structureReset(message) {
  structureRequest++; structureInfo = null; structureVersion = null; structureWorking = null;
  structureSelectedNode = null; structurePositions = new Map();
  const option = document.createElement('option'); option.value = ''; option.textContent = message;
  el('structure-select').replaceChildren(option);
  el('structure-version-line').textContent = 'Keine Struktur geladen.';
  el('structure-canvas').replaceChildren();
  structureHint('Knoten im Canvas anklicken.');
  el('structure-staging').textContent = 'Keine lokalen Änderungen.';
  const skeleton = el('structure-skeleton'); skeleton.replaceChildren();
  const placeholder = document.createElement('p'); placeholder.className = 'muted'; placeholder.textContent = 'Noch nicht generiert.';
  skeleton.append(placeholder);
  fillStructureEdgeSelects();
}
function fillStructureEdgeSelects() {
  const ids = structureWorking ? structureWorking.nodes.map(n => n.local_id).sort() : [];
  ['structure-edge-source', 'structure-edge-target'].forEach(id => {
    const keep = el(id).value;
    el(id).replaceChildren();
    ids.forEach(local => { const option = document.createElement('option'); option.value = local; option.textContent = local; el(id).append(option); });
    if (ids.includes(keep)) el(id).value = keep;
  });
}
function renderStagingNote() {
  if (!structureVersion || !structureWorking) { el('structure-staging').textContent = 'Keine lokalen Änderungen.'; return; }
  const saved = JSON.stringify({n: structureVersion.nodes, e: structureVersion.edges});
  const local = JSON.stringify({n: structureWorking.nodes, e: structureWorking.edges});
  el('structure-staging').textContent = saved === local
    ? `Keine lokalen Änderungen gegenüber Version ${structureVersion.version}.`
    : `Lokal vorbereitet — noch nicht versioniert: ${structureWorking.nodes.length} Knoten, ${structureWorking.edges.length} Beziehungen (gespeicherte Version ${structureVersion.version}: ${structureVersion.nodes.length}/${structureVersion.edges.length}).`;
}
function renderStructureCanvas() {
  const svg = el('structure-canvas');
  svg.replaceChildren();
  if (!structureWorking) return;
  const nodes = structureWorking.nodes, edges = structureWorking.edges;
  const parent = new Map(), kids = new Map();
  edges.filter(edge => edge.kind === 'contains').forEach(edge => { parent.set(edge.target, edge.source); kids.set(edge.source, [...(kids.get(edge.source) || []), edge.target]); });
  const roots = nodes.map(node => node.local_id).filter(id => !parent.has(id)).sort();
  const width = id => { const children = kids.get(id) || []; return children.length ? children.reduce((sum, child) => sum + width(child), 0) : 1; };
  structurePositions = new Map();
  const place = (id, depth, left) => {
    structurePositions.set(id, {x: left + width(id) * (NODE_W + 48) / 2, y: 40 + depth * (NODE_H + 100)});
    let childLeft = left;
    (kids.get(id) || []).slice().sort().forEach(child => { place(child, depth + 1, childLeft); childLeft += width(child) * (NODE_W + 48); });
  };
  let cursor = 0;
  roots.forEach(root => { place(root, 0, cursor * (NODE_W + 48)); cursor += width(root); });
  let stored = {};
  try { stored = JSON.parse(localStorage.getItem('atze-structure-positions-' + structureSelected) || '{}') || {}; } catch (error) { stored = {}; }
  Object.keys(stored).forEach(id => { if (structurePositions.has(id)) structurePositions.set(id, {x: stored[id].x, y: stored[id].y}); });
  if (!nodes.length) return;
  const xs = [...structurePositions.values()].map(p => p.x), ys = [...structurePositions.values()].map(p => p.y);
  const minX = Math.min(...xs) - NODE_W / 2 - 24, maxX = Math.max(...xs) + NODE_W / 2 + 24;
  const minY = Math.min(...ys) - NODE_H / 2 - 24, maxY = Math.max(...ys) + NODE_H / 2 + 24;
  svg.setAttribute('viewBox', `${minX} ${minY} ${maxX - minX} ${maxY - minY}`);
  const defs = svgElement('defs', {});
  const marker = svgElement('marker', {id: 'structure-arrow', viewBox: '0 0 10 10', refX: '9', refY: '5', markerWidth: '7', markerHeight: '7', orient: 'auto-start-reverse'});
  marker.append(svgElement('path', {d: 'M 0 0 L 10 5 L 0 10 z', fill: '#c9a86a'}));
  defs.append(marker); svg.append(defs);
  edges.forEach(edge => {
    const from = structurePositions.get(edge.source), to = structurePositions.get(edge.target);
    if (!from || !to) return;
    if (edge.kind === 'contains') {
      svg.append(svgElement('line', {x1: from.x, y1: from.y + NODE_H / 2, x2: to.x, y2: to.y - NODE_H / 2, stroke: '#6fae9c', 'stroke-width': '2'}));
    } else {
      const line = svgElement('line', {x1: from.x, y1: from.y, x2: to.x, y2: to.y, stroke: '#c9a86a', 'stroke-width': '1.5', 'stroke-dasharray': '6 5', 'marker-end': 'url(#structure-arrow)'});
      svg.append(line);
      const label = svgElement('text', {x: (from.x + to.x) / 2, y: (from.y + to.y) / 2 - 6, fill: '#c9a86a', 'font-size': '10', 'text-anchor': 'middle'});
      label.textContent = edge.kind;
      svg.append(label);
    }
  });
  const fills = {page: '#1d3a3f', section: '#233329', component: '#2a2333', action: '#33292a', data: '#23283a'};
  nodes.forEach(node => {
    const position = structurePositions.get(node.local_id) || {x: 0, y: 0};
    const group = svgElement('g', {transform: `translate(${position.x - NODE_W / 2},${position.y - NODE_H / 2})`, style: 'cursor:move'});
    group.append(svgElement('rect', {width: NODE_W, height: NODE_H, rx: 10, fill: fills[node.kind] || '#1d3a3f', stroke: structureSelectedNode === node.local_id ? '#f4d090' : '#53656a', 'stroke-width': '1.5'}));
    const title = svgElement('text', {x: 12, y: 26, fill: '#e4ecea', 'font-size': '13', 'font-weight': '600'});
    title.textContent = (node.name || '').slice(0, 22) + ((node.name || '').length > 22 ? '…' : '');
    const subtitle = svgElement('text', {x: 12, y: 46, fill: '#a1b4b5', 'font-size': '11'});
    subtitle.textContent = `${node.kind} · ${node.local_id}`;
    group.append(title, subtitle);
    group.addEventListener('pointerdown', structureNodeDrag(node.local_id, group));
    group.addEventListener('click', () => { if (structureSuppressClick) { structureSuppressClick = false; return; } inspectStructureNode(node.local_id); });
    svg.append(group);
  });
}
function persistStructurePositions() {
  if (!structureSelected) return;
  const data = {};
  structurePositions.forEach((position, id) => { data[id] = position; });
  try { localStorage.setItem('atze-structure-positions-' + structureSelected, JSON.stringify(data)); } catch (error) { /* Ansichtspositionen sind optional; Modell bleibt unberührt. */ }
}
function structureNodeDrag(localId, group) {
  return event => {
    if (!structureWorking) return;
    if (event.pointerType === 'mouse' && event.button !== 0) return;
    event.preventDefault();
    const svg = el('structure-canvas');
    const start = svgPoint(svg, event.clientX, event.clientY);
    const origin = structurePositions.get(localId) || {x: 0, y: 0};
    let moved = false;
    const move = moveEvent => {
      const current = svgPoint(svg, moveEvent.clientX, moveEvent.clientY);
      const next = {x: origin.x + current.x - start.x, y: origin.y + current.y - start.y};
      if (Math.abs(current.x - start.x) + Math.abs(current.y - start.y) > 3) moved = true;
      structurePositions.set(localId, next);
      group.setAttribute('transform', `translate(${next.x - NODE_W / 2},${next.y - NODE_H / 2})`);
    };
    const finish = () => {
      window.removeEventListener('pointermove', move);
      window.removeEventListener('pointerup', finish);
      if (moved) { structureSuppressClick = true; persistStructurePositions(); renderStructureCanvas(); status('Ansichtsposition verschoben — das Modell selbst ist unverändert.'); }
    };
    window.addEventListener('pointermove', move);
    window.addEventListener('pointerup', finish);
  };
}
function inspectStructureNode(localId) {
  const box = el('structure-inspector');
  box.replaceChildren();
  const node = structureWorking && structureWorking.nodes.find(candidate => candidate.local_id === localId);
  if (!node) { structureHint('Knoten nicht im lokalen Modell vorhanden.'); return; }
  structureSelectedNode = localId;
  const head = document.createElement('p');
  head.textContent = `${node.kind} · ${node.local_id}` + (node.permissions && node.permissions.length ? ` · Berechtigungen (deklarativ): ${node.permissions.join(', ')}` : ' · keine Berechtigungen deklariert');
  box.append(head);
  const form = document.createElement('form');
  const nameLabel = document.createElement('label'); nameLabel.textContent = 'Name';
  const name = document.createElement('input'); name.required = true; name.maxLength = 120; name.value = node.name || '';
  nameLabel.append(name);
  const permissionsLabel = document.createElement('label'); permissionsLabel.textContent = 'Berechtigungen (Komma-getrennt, deklarativ — keine durchgesetzte Autorisierung)';
  const permissions = document.createElement('input'); permissions.maxLength = 200; permissions.value = (node.permissions || []).join(', ');
  permissionsLabel.append(permissions);
  const noteLabel = document.createElement('label'); noteLabel.textContent = 'Notiz';
  const note = document.createElement('textarea'); note.maxLength = 2000; note.value = node.note || '';
  noteLabel.append(note);
  const apply = document.createElement('button'); apply.textContent = 'Änderung übernehmen (Staging)';
  const remove = document.createElement('button'); remove.type = 'button'; remove.textContent = 'Knoten entfernen (Staging)';
  form.append(nameLabel, permissionsLabel, noteLabel, apply, remove);
  form.onsubmit = submitEvent => {
    submitEvent.preventDefault();
    const target = structureWorking.nodes.find(candidate => candidate.local_id === localId);
    if (!target) return;
    target.name = name.value.trim();
    target.permissions = permissions.value.split(',').map(entry => entry.trim()).filter(Boolean);
    target.note = note.value;
    renderStructureCanvas(); renderStagingNote(); inspectStructureNode(localId);
    status('Knoten lokal übernommen — noch nicht versioniert.');
  };
  remove.onclick = () => {
    structureWorking.nodes = structureWorking.nodes.filter(candidate => candidate.local_id !== localId);
    structureWorking.edges = structureWorking.edges.filter(edge => edge.source !== localId && edge.target !== localId);
    structureSelectedNode = null;
    structureHint('Knoten im Canvas anklicken.');
    renderStructureCanvas(); renderStagingNote(); fillStructureEdgeSelects();
    status('Knoten und seine Beziehungen lokal entfernt — noch nicht versioniert.');
  };
  box.append(form);
  const relations = document.createElement('p');
  const touching = structureWorking.edges.filter(edge => edge.source === localId || edge.target === localId);
  relations.textContent = touching.length ? 'Beziehungen: ' + touching.map(edge => `${edge.source} —${edge.kind}→ ${edge.target}`).join(' · ') : 'Keine Beziehungen.';
  box.append(relations);
}
async function renderGenerated(id) {
  const generated = await api(`structures/${id}/generate`);
  list('structure-routes', generated.routes, (node, route) => { node.textContent = `${route.path} → ${route.title} (${route.node})`; });
  const skeleton = el('structure-skeleton');
  skeleton.replaceChildren();
  const meta = document.createElement('p'); meta.className = 'muted';
  meta.textContent = `Version ${generated.version} · CALCULATED aus STRUCTURE_VERSION_MANIFEST · SHA-256 ${generated.manifest_hash} · Platzhalter EMPTY · keine Prognose, keine Aktionsfreigabe.`;
  skeleton.append(meta);
  const addLevel = (children, container) => {
    const listNode = document.createElement('ul');
    children.forEach(child => {
      const item = document.createElement('li');
      item.textContent = `${child.title} [${child.kind}] EMPTY` +
        (child.permissions && child.permissions.length ? ` · Berechtigungen (deklarativ): ${child.permissions.join(', ')}` : '') +
        (child.relations && child.relations.length ? ` · ${child.relations.map(relation => `${relation.kind} von ${relation.from}`).join(' · ')}` : '');
      if (child.children) addLevel(child.children, item);
      listNode.append(item);
    });
    container.append(listNode);
  };
  addLevel(generated.ui_skeleton.roots, skeleton);
  return generated;
}
async function loadStructure(id) {
  const current = session, request = ++structureRequest;
  structureSelected = id; structureSelectedNode = null;
  el('structure-version-line').textContent = 'Lade Struktur…';
  structureHint('Knoten im Canvas anklicken.');
  try {
    const [structure, versions] = await Promise.all([api(`structures/${id}`), api(`structures/${id}/versions?limit=1`)]);
    if (current !== session || request !== structureRequest || id !== structureSelected) return;
    const version = versions[0];
    structureInfo = structure; structureVersion = version;
    structureWorking = {nodes: version.nodes.map(node => ({...node, permissions: [...(node.permissions || [])]})), edges: version.edges.map(edge => ({...edge}))};
    el('structure-version-line').textContent = `Struktur ${structure.name} · ${structure.state === 'active' ? 'aktiv' : 'deaktiviert'} · Version ${version.version} · SHA-256 ${version.manifest_hash.slice(0, 12)}…`;
    renderStructureCanvas(); renderStagingNote(); fillStructureEdgeSelects();
    await renderGenerated(id);
  } catch (error) {
    if (current === session && request === structureRequest) { structureReset('Struktur nicht verfügbar.'); status(error.message); }
  }
}
el('structure-select').onchange = () => {
  const id = el('structure-select').value;
  if (id) loadStructure(id); else structureReset('Keine Struktur ausgewählt.');
};
el('structure-add').onsubmit = async event => {
  event.preventDefault(); const current = session;
  const data = Object.fromEntries(new FormData(event.target));
  try {
    const structure = await api('structures', 'POST', {name: data.name, description: data.description || '',
      nodes: [{local_id: 'root', kind: 'page', name: data.root_name.trim(), permissions: [], note: 'Wurzel-Seite aus der Oberfläche'}],
      edges: [], note: 'Angelegt über die Oberfläche'});
    if (current !== session) return;
    event.target.reset();
    structurePendingSelect = structure.id;
    status(`Struktur angelegt (+): ${structure.id} · Version 1. Weitere Knoten jetzt lokal vorbereiten und als neue Version committen.`);
    await refresh();
  } catch (error) { if (current === session) status(error.message); }
};
el('structure-node-add').onsubmit = event => {
  event.preventDefault();
  if (!structureWorking) { status('Zuerst eine Struktur laden.'); return; }
  const data = Object.fromEntries(new FormData(event.target));
  const localId = data.local_id.trim();
  if (!/^[a-z0-9][a-z0-9_-]{0,63}$/.test(localId)) { status('Kennung: Kleinbuchstaben, Ziffern, „-“ und „_“; Beginn mit Buchstabe oder Ziffer.'); return; }
  if (structureWorking.nodes.some(node => node.local_id === localId)) { status('Diese Kennung existiert bereits im lokalen Modell.'); return; }
  structureWorking.nodes.push({local_id: localId, kind: data.kind, name: data.name.trim(),
    permissions: data.permissions.split(',').map(entry => entry.trim()).filter(Boolean), note: data.note || ''});
  event.target.reset();
  renderStructureCanvas(); renderStagingNote(); fillStructureEdgeSelects();
  status('Knoten lokal vorbereitet — noch nicht versioniert.');
};
el('structure-edge-add').onsubmit = event => {
  event.preventDefault();
  if (!structureWorking) { status('Zuerst eine Struktur laden.'); return; }
  const data = Object.fromEntries(new FormData(event.target));
  const source = el('structure-edge-source').value, target = el('structure-edge-target').value;
  if (!source || !target) { status('Quelle und Ziel auswählen.'); return; }
  if (source === target) { status('Quelle und Ziel müssen unterschiedlich sein.'); return; }
  if (structureWorking.edges.some(edge => edge.source === source && edge.target === target && edge.kind === data.kind)) { status('Diese Beziehung existiert bereits im lokalen Modell.'); return; }
  structureWorking.edges.push({source, target, kind: data.kind});
  renderStructureCanvas(); renderStagingNote();
  status('Beziehung lokal vorbereitet — noch nicht versioniert.');
};
el('structure-discard').onclick = () => {
  if (!structureVersion) { status('Keine gespeicherte Version zum Wiederherstellen geladen.'); return; }
  structureWorking = {nodes: structureVersion.nodes.map(node => ({...node, permissions: [...(node.permissions || [])]})), edges: structureVersion.edges.map(edge => ({...edge}))};
  structureSelectedNode = null;
  structureHint('Knoten im Canvas anklicken.');
  renderStructureCanvas(); renderStagingNote(); fillStructureEdgeSelects();
  status('Lokale Entwürfe verworfen — gespeicherte Version wiederhergestellt.');
};
el('structure-commit').onsubmit = async event => {
  event.preventDefault(); const current = session;
  if (!structureSelected || !structureWorking) { status('Zuerst eine Struktur laden.'); return; }
  const note = Object.fromEntries(new FormData(event.target)).note;
  try {
    const version = await api(`structures/${structureSelected}/versions`, 'POST', {nodes: structureWorking.nodes, edges: structureWorking.edges, note});
    if (current !== session) return;
    event.target.reset();
    status(`Version ${version.version} committet (Manifest SHA-256 ${version.manifest_hash.slice(0, 12)}…). Vorherige Versionen bleiben unverändert.`);
    await loadStructure(structureSelected);
  } catch (error) { if (current === session) status(error.message); }
};
el('structure-generate').onclick = async () => {
  if (!structureSelected) { status('Zuerst eine Struktur laden.'); return; }
  const current = session;
  try {
    const generated = await renderGenerated(structureSelected);
    if (current === session) status(`Generierung abgeschlossen: ${generated.routes.length} Routen · Version ${generated.version} (Query ohne Nebenwirkungen).`);
  } catch (error) { if (current === session) status(error.message); }
};
