/* Real Chromium CDP over inherited pipes, no driver dependency or fake DOM.
   Only smoke.py's fresh local test instance + ephemeral stdin credentials.
   No external URL/CLI credential accepted, no --no-sandbox fallback. */
'use strict';
const {spawn, execFileSync} = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const assert = (value, name) => { if (!value) throw new Error(name); };
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
(async () => {
  const report = {kind:'REAL CHROMIUM / SYNTHETIC TEST INPUTS',status:'FAIL',checks:[],started_at:new Date().toISOString()};
  let chrome, profile, closeBrowser;
  try {
    const config = JSON.parse(fs.readFileSync(0,'utf8'));
    assert(/^http:\/\/127\.0\.0\.1:\d+$/.test(config.url), 'Only disposable loopback test Core accepted');
    const api = async (route, method='GET', body, reviewer=false) => {
      const response = await fetch(config.url+route,{method,headers:{Authorization:`Bearer ${reviewer?config.reviewer:config.operator}`,'Content-Type':'application/json'},body:body?JSON.stringify(body):undefined,signal:AbortSignal.timeout(10000),redirect:'error'});
      assert(response.ok, `Real fixture API failed: ${method} ${route.split('/').slice(0,3).join('/')} ${response.status}`);
      return response.json();
    };
    assert((await api('/api/runtime')).mode==='test','Browser inputs forbidden outside test mode');
    const binary = ['/usr/bin/google-chrome','/usr/bin/chromium','/usr/bin/chromium-browser'].find(p=>fs.existsSync(p));
    assert(binary,'Real Chromium not installed; browser gate BLOCKED');
    report.browser=execFileSync(binary,['--version'],{encoding:'utf8'}).trim();
    profile=fs.mkdtempSync(path.join(os.tmpdir(),'atze-browser-'));
    let diagnostic='';
    chrome=spawn(binary,['--headless=new','--remote-debugging-pipe','--no-startup-window',`--user-data-dir=${profile}`,'--disable-background-networking','--disable-component-update','--disable-sync','--no-first-run','--disable-default-apps','--metrics-recording-only'],{stdio:['ignore','ignore','pipe','pipe','pipe']});
    chrome.stderr.on('data',chunk=>{ diagnostic=(diagnostic+chunk.toString()).slice(-8192); });
    chrome.once('exit',()=>{
      // Bounded startup cause only, no raw profile logs/paths, inputs or credentials.
      if(/No usable sandbox|Failed to move to new namespace|SUID sandbox|sandbox_host_linux/.test(diagnostic)) report.startup_cause='CHROMIUM_SANDBOX_UNAVAILABLE';
      else if(/DevTools remote debugging requires/.test(diagnostic)) report.startup_cause='CHROMIUM_DEBUG_PIPE_REJECTED';
    });
    let next=0,buffer='',session;
    const pending=new Map();
    chrome.stdio[4].on('data',chunk=>{
      buffer+=chunk.toString(); let end;
      while((end=buffer.indexOf('\0'))!==-1){
        const message=JSON.parse(buffer.slice(0,end)); buffer=buffer.slice(end+1);
        if(pending.has(message.id)){
          const {resolve,reject,timer}=pending.get(message.id); pending.delete(message.id); clearTimeout(timer);
          if(message.error) reject(new Error('Chromium protocol rejected command')); else resolve(message.result);
        }
      }
    });
    const failPending=()=>{for(const {reject,timer} of pending.values()){clearTimeout(timer);reject(new Error('Chromium exited or pipe closed'));} pending.clear();};
    chrome.on('exit',failPending); chrome.on('error',failPending); chrome.stdio[3].on('error',failPending);
    const cdp=(method,params={},sid=session)=>new Promise((resolve,reject)=>{
      const id=++next; const timer=setTimeout(()=>{pending.delete(id);reject(new Error('Chromium protocol timeout'));},15000);
      pending.set(id,{resolve,reject,timer}); chrome.stdio[3].write(JSON.stringify({id,method,params,...(sid?{sessionId:sid}:{})})+'\0');
    });
    closeBrowser=()=>cdp('Browser.close',{},null);
    const target=await cdp('Target.createTarget',{url:config.url});
    session=(await cdp('Target.attachToTarget',{targetId:target.targetId,flatten:true})).sessionId;
    const evaluate=async expression=>{
      const result=await cdp('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});
      assert(!result.exceptionDetails,'Browser evaluation failed'); return result.result.value;
    };
    const wait=async(expression,name)=>{for(let i=0;i<100;i++){if(await evaluate(expression))return;await pause(50);}throw new Error(name);};
    const check=name=>report.checks.push({id:name,status:'PASS',actual:'Browser DOM + real API assertions passed'});
    await wait("document.readyState==='complete' && ['login','project','refresh','context-search','results','ai-lock','plan-editor'].every(id=>!!document.getElementById(id))",'Dashboard UI did not load');
    const p=await api('/api/projects','POST',{name:'Explicit synthetic browser project',description:'Temporary CI input only'});
    const e=await api('/api/evidence','POST',{project_id:p.id,claim:'Explicit synthetic browser source',source_url:'https://example.org/isolated-browser-input',observed_at:'2026-01-01T00:00:00Z',source_type:'manual',provider:'isolated browser validation',extraction_method:'manual',content:'Synthetic text; never live device evidence',confidence:0.9});
    const task=await api('/api/tasks','POST',{project_id:p.id,title:'Browser test task',action:'read',evidence_ids:[e.id],preconditions_met:true});
    await api('/api/archive','POST',{project_id:p.id,relative_path:'browser-input.txt',content:'Selected synthetic browser archive'});
    const login=async token=>{
      assert(!(await evaluate(`document.getElementById('token').value=${JSON.stringify(token)}; document.getElementById('login').requestSubmit(); document.getElementById('status').textContent.startsWith('Verbunden.')`)), 'Old connected status survived new login');
      await wait("document.getElementById('status').textContent.startsWith('Verbunden.')",'Authenticated refresh failed');
    };
    await login(config.operator);
    await evaluate("document.getElementById('status').textContent='Manually refreshed test sentinel'; document.getElementById('refresh').click()");
    await wait("document.getElementById('status').textContent.startsWith('Verbunden.')",'Dashboard refresh did not fetch workspace data');
    assert(await evaluate("document.getElementById('runtime-mode').textContent.startsWith('TESTINSTANZ') && document.getElementById('projects').textContent.length>0"),'Dashboard did not render authenticated runtime/project data'); check('BROWSER-DASHBOARD-01-LOGIN-REFRESH');
    const createdProject='Browser form project';
    await evaluate(`(()=>{const form=document.getElementById('project');form.querySelector('[name=name]').value=${JSON.stringify(createdProject)};form.querySelector('[name=description]').value='Created through the real dashboard form';form.requestSubmit()})()`);
    await wait(`document.getElementById('projects').textContent.includes(${JSON.stringify(createdProject)})`,'Project form did not refresh the real project list');
    assert((await api('/api/projects')).some(row=>row.name===createdProject),'Dashboard project form did not persist through API'); check('BROWSER-DASHBOARD-02-PROJECT-CREATE');
    await evaluate(`(()=>{const row=[...document.querySelectorAll('#tasks li')].find(node=>node.textContent.includes(${JSON.stringify(task.id)}));if(!row)throw new Error('browser task missing');row.querySelector('button').click()})()`);
    await wait("document.getElementById('status').textContent.startsWith('blocked:')",'Triage UI did not report the actual blocked decision');
    const dashboardTriage=await api(`/api/tasks/${task.id}/triage`,'POST');
    assert(dashboardTriage.state==='blocked' && dashboardTriage.executed===false,'Triage UI path could imply execution'); check('BROWSER-DASHBOARD-03-TRIAGE-NO-EXECUTION');
    await evaluate(`(()=>{document.getElementById('context-project').value=${JSON.stringify(p.id)};const form=document.getElementById('context-search');form.querySelector('[name=query]').value='Selected synthetic browser archive';form.requestSubmit()})()`);
    await wait("document.getElementById('context-hits').textContent.includes('browser-input.txt')",'Context search UI did not render the real archive hit'); check('BROWSER-DASHBOARD-04-CONTEXT-SEARCH');
    const browserResult=(await api('/api/results')).find(row=>row.claims.length && row.claims[0].evidence_ids.length);
    assert(browserResult,'Smoke fixture did not provide a result for dashboard inspection');
    const resultRow=`[...document.querySelectorAll('#results li')].find(node=>node.textContent.includes(${JSON.stringify(browserResult.id)}))`;
    await evaluate(`(()=>{const row=${resultRow};if(!row)throw new Error('result missing');[...row.querySelectorAll('button')].find(button=>button.textContent==='Warum?').click()})()`);
    await wait("document.getElementById('challenge-detail').textContent.includes('Primärtext')",'Result Why UI did not read real challenge metadata');
    assert(await evaluate(`document.getElementById('challenge-detail').textContent.includes(${JSON.stringify(browserResult.id)})`),'Result Why UI did not bind the selected real result');
    await evaluate(`(()=>{const row=${resultRow};[...row.querySelectorAll('button')].find(button=>button.textContent==='Quellen').click()})()`);
    await wait(`document.getElementById('challenge-detail').textContent.includes(${JSON.stringify('Evidence '+browserResult.claims[0].evidence_ids[0])})`,'Result Sources UI did not read the referenced real evidence'); check('BROWSER-DASHBOARD-05-RESULT-WHY-SOURCES');
    await evaluate(`(()=>{const row=${resultRow};[...row.querySelectorAll('button')].find(button=>button.textContent==='Herausfordern').click();const form=row.querySelector('form');if(form.hidden)throw new Error('challenge form hidden');form.querySelector('input').value='Explicit dashboard re-challenge';form.requestSubmit()})()`);
    await wait("document.getElementById('status').textContent.includes('angefordert')",'Result challenge UI did not queue a real challenge');
    assert((await api(`/api/results/${browserResult.id}/why`)).latest_job.state==='pending','Dashboard challenge did not leave a pending separate-worker job'); check('BROWSER-DASHBOARD-06-RESULT-RECHALLENGE');
    await evaluate("document.getElementById('plan-title').value='Discard this dashboard draft';document.getElementById('plan-reset').click()");
    assert(await evaluate("document.getElementById('plan-title').value==='' && document.getElementById('plan-id').value==='' && document.getElementById('plan-version-id').value===''"),'New PLAN button retained draft state'); check('BROWSER-PLAN-00-RESET-DRAFT');
    await evaluate(`document.getElementById('plan-task').value=${JSON.stringify(task.id)}; document.getElementById('plan-task').dispatchEvent(new Event('change'))`);
    assert(await evaluate("document.getElementById('plan-resources').options.length===2"),'Project/task selection did not filter actual resources');
    const title='Synthetic PLAN <img src=x onerror="window.__planXss=true">';
    await evaluate(`document.getElementById('plan-title').value=${JSON.stringify(title)}; [...document.getElementById('plan-resources').options].forEach(o=>o.selected=true); document.getElementById('plan-editor').requestSubmit()`);
    await wait(`document.getElementById('plans').textContent.includes(${JSON.stringify(task.id)})`,'PLAN create did not finish');
    const plan=(await api('/api/plans')).find(p=>p.task_id===task.id);
    assert(plan,'Browser did not create a real PLAN'); check('BROWSER-PLAN-01-CREATE-TWO-REAL-SOURCES');
    const detail=async()=>{
      await evaluate(`[...document.querySelectorAll('#plans li')].find(n=>n.textContent.includes(${JSON.stringify(plan.id)})).querySelector('button').click()`);
      await wait("!!document.querySelector('#plan-detail form')",'PLAN detail did not load');
    };
    await detail();
    assert(await evaluate("!document.querySelector('#plan-detail img') && !window.__planXss"),'Untrusted title executed markup');
    assert(await evaluate(`document.getElementById('plan-detail').textContent.includes(${JSON.stringify(title)})`),'Actual title not rendered as text'); check('BROWSER-PLAN-02-TEXTCONTENT-XSS');
    await evaluate("document.querySelector('#plan-detail input').value='Isolated wrong-role test'; document.querySelector('#plan-detail form').requestSubmit()");
    await wait("document.getElementById('status').textContent.includes('403')",'Operator unexpectedly locked context');
    assert((await api(`/api/plans/${plan.id}/status`)).state==='UNLOCKED','Wrong role acquired context lock'); check('BROWSER-PLAN-03-ROLE-DENY');
    await login(config.reviewer); await detail();
    await evaluate("document.querySelector('#plan-detail input').value='Explicit browser context review'; document.querySelector('#plan-detail form').requestSubmit()");
    await wait("document.getElementById('plan-detail').textContent.startsWith('CURRENT:')",'Reviewer context lock failed');
    assert((await api(`/api/plans/${plan.id}/status`)).state==='CURRENT','UI lock not persisted'); check('BROWSER-PLAN-04-REVIEWER-LOCK');
    await evaluate("document.querySelector('#plan-detail input').value='Explicit browser revoke'; [...document.querySelectorAll('#plan-detail button')].find(b=>b.textContent.includes('widerrufen')).click()");
    await wait("document.getElementById('plan-detail').textContent.startsWith('REVOKED:')",'Reviewer revoke failed');
    assert((await api(`/api/plans/${plan.id}/status`)).state==='REVOKED','UI revoke not persisted'); check('BROWSER-PLAN-05-REVOKE');
    await evaluate("document.getElementById('ai-lock').click()");
    await wait("document.getElementById('status').textContent.startsWith('KI gesperrt:')",'Reviewer AI lock did not complete through dashboard');
    const aiStatus=await api('/api/ai/status','GET',undefined,true);
    assert(aiStatus.policy.privacy_lock && aiStatus.policy.local_only && !aiStatus.policy.external_ai,'Dashboard AI lock did not persist the restrictive policy');
    assert(await evaluate("document.getElementById('ai-policy-state').textContent.includes('Privacy Lock: AN') && document.getElementById('ai-policy-state').textContent.includes('External AI: DENY')"),'Dashboard did not render the restrictive AI policy'); check('BROWSER-DASHBOARD-07-AI-LOCAL-LOCK');
    await login(config.operator);
    await evaluate(`[...document.querySelectorAll('#plans li')].find(n=>n.textContent.includes(${JSON.stringify(plan.id)})).querySelectorAll('button')[1].click()`);
    await wait("!!document.getElementById('plan-version-id').value",'Version editor did not initialize');
    await evaluate("document.getElementById('plan-title').value='Actual second browser version'; document.getElementById('plan-editor').requestSubmit()");
    await wait("document.getElementById('plan-version-id').value===''",'Revision did not finish');
    assert((await api(`/api/plans/${plan.id}/versions`))[0].version===2,'Browser revision not append-only'); check('BROWSER-PLAN-06-IMMUTABLE-REVISION');
    await evaluate(`document.getElementById('token').value=${JSON.stringify(config.operator)}; document.getElementById('logout').click()`);
    assert(await evaluate("document.getElementById('token').value==='' && document.getElementById('plan-detail').textContent==='' && !document.getElementById('plan-resources').options.length"),'Logout retained PLAN source UI'); check('BROWSER-PLAN-07-LOGOUT-CLEAR');
    report.status='PASS';
  } catch(error){report.error=error.message; process.exitCode=1;}
  finally {
    if(chrome && chrome.exitCode===null && chrome.signalCode===null){
      const exited=new Promise(resolve=>chrome.once('exit',resolve));
      if(closeBrowser){try{await closeBrowser();}catch(error){report.close_protocol='UNAVAILABLE_SIGNAL_CLEANUP_REQUIRED';}}
      await Promise.race([exited,pause(1000)]);
      if(chrome.exitCode===null && chrome.signalCode===null) chrome.kill('SIGTERM');
      await Promise.race([exited,pause(3000)]);
      if(chrome.exitCode===null && chrome.signalCode===null){chrome.kill('SIGKILL');await Promise.race([exited,pause(3000)]);}
    }
    report.browser_stopped=!chrome || chrome.exitCode!==null || chrome.signalCode!==null;
    if(!report.browser_stopped){report.status='FAIL';process.exitCode=1;}
    if(profile){
      try {fs.rmSync(profile,{recursive:true,force:true,maxRetries:5,retryDelay:100});}
      catch(error){report.cleanup_error=error.code || 'PROFILE_CLEANUP_FAILED';report.status='FAIL';process.exitCode=1;}
    }
    report.finished_at=new Date().toISOString(); process.stdout.write(JSON.stringify(report)+'\n');
  }
})();
