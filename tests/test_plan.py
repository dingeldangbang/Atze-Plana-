"""Real isolated PLAN API/SQLite/files/HTTP, synthetic test inputs only."""
import json
import sqlite3
import pytest
from app.store import Store
from app.plan_service import task_gate
from conftest import seed, task, challenged_result, process_job_api
from test_ai_privacy import ai, receiver


def make(client, reviewer, *, tid=None, eid=None, resources=None):
    if tid is None:
        project, evidence = seed(client, reviewer)
        tid, eid = task(client, project, evidence), evidence['id']
    body = {'task_id':tid,'title':'Isolated PLAN inputs','resources':resources or [{'kind':'evidence','id':eid}]}
    response = client.post('/api/plans',json=body)
    assert response.status_code==201, response.text
    plan=response.json()
    version=client.get(f"/api/plans/{plan['id']}/versions").json()[0]
    return plan,version,body


def lock(client, reviewer, plan, version):
    response=client.post(f"/api/plans/{plan['id']}/locks",headers=reviewer,json={'version_id':version['id'],'manifest_hash':version['manifest_hash'],'reason':'Explicit isolated context review'})
    assert response.status_code==201,response.text
    return response.json()


def state(client, plan):
    return client.get(f"/api/plans/{plan['id']}/status").json()


def test_plan_real_multi_resource_manifest(client, reviewer):
    """PLAN-001 | selected real sources | temp evidence/memory/archive | create/lock | hashes/provenance only, no truth/permissions | asserted."""
    p,e=seed(client,reviewer);tid=task(client,p,e)
    m=client.post('/api/memory',json={'project_id':p['id'],'task_id':tid,'category':'inference','content':'synthetic private PLAN text','evidence_ids':[e['id']]}).json()
    a=client.post('/api/archive',json={'project_id':p['id'],'relative_path':'actual-test.txt','content':'  synthetic archive input\n','evidence_ids':[e['id']]}).json()
    refs=[{'kind':k,'id':v['id']} for k,v in [('evidence',e),('memory',m),('archive',a)]]
    plan,v,body=make(client,reviewer,tid=tid,resources=refs)
    assert state(client,plan)['state']=='UNLOCKED'
    assert 'synthetic private PLAN text' not in json.dumps(v)
    assert [r['sha256'] for r in v['manifest']['resources']]==[e['sha256'],m['sha256'],a['sha256']]
    assert all(r['truth_status']=='UNKNOWN' and r['content_integrity']=='VERIFIED' for r in v['manifest']['resources'])
    lock(client,reviewer,plan,v)
    assert state(client,plan)['state']=='CURRENT' and not state(client,plan)['allowed_for_action']
    assert client.post('/api/plans',json=body).status_code==409
    assert client.get('/api/plans').json()==[plan]


def test_plan_roles_and_immutable_versions(client,reviewer):
    """PLAN-002 | role/optimistic boundaries | current lock | append old/new versions | wrong roles/stale expectations blocked."""
    plan,v,body=make(client,reviewer)
    payload={'version_id':v['id'],'manifest_hash':v['manifest_hash'],'reason':'Explicit isolated review'}
    assert client.post(f"/api/plans/{plan['id']}/locks",json=payload).status_code==403
    assert client.post('/api/plans',headers=reviewer,json=body).status_code==403
    oldlock=lock(client,reviewer,plan,v)
    revise={k:value for k,value in body.items() if k!='task_id'}
    revise['expected_version_id']='wrong'
    url=f"/api/plans/{plan['id']}/versions"
    assert client.post(url,json=revise).status_code==409
    revise['expected_version_id']=v['id'];revise['title']='New actual version'
    assert client.post(url,headers=reviewer,json=revise).status_code==403
    nv=client.post(url,json=revise).json()
    assert nv['version']==2 and state(client,plan)['state']=='SUPERSEDED'
    assert client.post(f"/api/plans/{plan['id']}/locks",headers=reviewer,json=payload).status_code==409
    assert client.get(url).json()[1]==v
    lock(client,reviewer,plan,nv)
    assert state(client,plan)['lock_id']!=oldlock['id']


def test_plan_stop_and_revocation(client,reviewer):
    """PLAN-003 | stop/reset/revoke | actual control audit | lock then stop | no revived lock, revoke allowed during stop."""
    plan,v,body=make(client,reviewer);l=lock(client,reviewer,plan,v)
    client.post('/api/control/stop',headers=reviewer,json={'active':True,'reason':'Isolated stop test'})
    assert state(client,plan)['state']=='BLOCKED'
    assert client.post(f"/api/plans/{plan['id']}/locks",headers=reviewer,json={'version_id':v['id'],'manifest_hash':v['manifest_hash'],'reason':'Cannot lock under stop'}).status_code==409
    client.post('/api/control/stop',headers=reviewer,json={'active':False,'reason':'Reset is not old approval'})
    assert state(client,plan)['state']=='STALE'
    client.post('/api/control/stop',headers=reviewer,json={'active':True,'reason':'Stop before revoke'})
    path=f"/api/plan-locks/{l['id']}/revoke"
    assert client.post(path,json={'reason':'Wrong role'}).status_code==403
    assert client.post(path,headers=reviewer,json={'reason':'Explicit revoke'}).status_code==200
    assert client.post(path,headers=reviewer,json={'reason':'Duplicate revoke'}).status_code==409
    client.post('/api/control/stop',headers=reviewer,json={'active':False,'reason':'Resume without restoring grant'})
    assert state(client,plan)['state']=='REVOKED'


def test_plan_isolation_and_missing_sources(client,reviewer):
    """PLAN-004 | referential integrity | actual two projects/tasks | foreign/duplicate/missing/unsupported refs | 422/404 and rollback."""
    p,e=seed(client,reviewer);tid=task(client,p,e)
    foreign,fe=seed(client,reviewer)
    body={'task_id':tid,'title':'Isolated test','resources':[{'kind':'evidence','id':fe['id']}]}
    assert client.post('/api/plans',json=body).status_code==422
    assert client.get('/api/plans').json()==[]
    body['resources']=[{'kind':'evidence','id':'missing'}]
    assert client.post('/api/plans',json=body).status_code==404
    body['resources']=[{'kind':'evidence','id':e['id']}]*2
    assert client.post('/api/plans',json=body).status_code==422
    body['resources']=[{'kind':'device','id':'not-a-device'}]
    assert client.post('/api/plans',json=body).status_code==422
    m=client.post('/api/memory',json={'project_id':p['id'],'task_id':task(client,p,e),'category':'inference','content':'Synthetic other task','evidence_ids':[]}).json()
    body['resources']=[{'kind':'memory','id':m['id']}]
    assert client.post('/api/plans',json=body).status_code==422


def test_plan_corrupt_archive_blocks_triage_and_adopt(client,reviewer,settings):
    """PLAN-005 | actual file mutation | challenged task with archive lock | corrupt blob | lock/triage/adopt BLOCK, no hidden IO fallback."""
    p,e=seed(client,reviewer);tid=task(client,p,e)
    a=client.post('/api/archive',json={'project_id':p['id'],'relative_path':'plan.txt','content':'Synthetic archive'}).json()
    plan,v,_=make(client,reviewer,tid=tid,resources=[{'kind':'archive','id':a['id']}]);lock(client,reviewer,plan,v)
    result=challenged_result(client,tid,e['id'])
    assert client.post(f'/api/tasks/{tid}/triage').json()['state']=='eligible'
    with Store(settings.db_path,'test').connect() as db:
        assert task_gate(db,tid)['state']=='BLOCKED' # storage omitted must not pretend hash verification
    (settings.db_path.parent/'objects'/(a['key']+'.blob')).write_bytes(b'corrupt')
    assert state(client,plan)['state']=='BLOCKED'
    assert client.post(f'/api/tasks/{tid}/triage').json()['state']=='blocked'
    assert client.post(f"/api/results/{result['id']}/adopt",headers=reviewer,json={'reason':'Must not adopt corrupt context'}).status_code==409
    client.post(f"/api/results/{result['id']}/challenge",json={'reason':'Check blocked context'})
    report=process_job_api(client)
    assert report['analysis']['verdict']=='BLOCK'
    assert any(f['code']=='PLAN_CONTEXT_NOT_CURRENT' for f in report['analysis']['findings'])


def test_plan_source_review_staleness_and_lock_hash(client,reviewer):
    """PLAN-006 | exact source state | unreviewed source selected | review changes metadata | stale/hash mismatch refuses lock."""
    p,e=seed(client,reviewer,verified=False);tid=task(client,p,e)
    plan,v,_=make(client,reviewer,tid=tid,eid=e['id']);lock(client,reviewer,plan,v)
    client.post(f"/api/evidence/{e['id']}/review",headers=reviewer,json={'state':'verified','reason':'Actual synthetic review transition'})
    assert state(client,plan)['state']=='STALE'
    assert client.post(f"/api/plans/{plan['id']}/locks",headers=reviewer,json={'version_id':v['id'],'manifest_hash':v['manifest_hash'],'reason':'Old manifest forbidden'}).status_code==409


def test_plan_version_invalidates_approval_and_rag(client,reviewer):
    """PLAN-007 | entire decision chain | real challenge/approval/adopt | append PLAN version | approval and RAG decision invalidated."""
    p,e=seed(client,reviewer);tid=task(client,p,e,action='write')
    plan,v,body=make(client,reviewer,tid=tid,eid=e['id']);lock(client,reviewer,plan,v)
    result=challenged_result(client,tid,e['id'])
    assert client.post(f'/api/tasks/{tid}/approve',headers=reviewer,json={'reason':'Explicit synthetic approval'}).status_code==201
    memory=client.post(f"/api/results/{result['id']}/adopt",headers=reviewer,json={'reason':'Explicit bounded decision'}).json()
    query={'project_id':p['id'],'query':'Structured claims'}
    assert next(h for h in client.post('/api/context/query',json=query).json() if h['source_id']==memory['id'])['decision_status']=='ACCEPT'
    revision={k:value for k,value in body.items() if k!='task_id'};revision['expected_version_id']=v['id']
    nv=client.post(f"/api/plans/{plan['id']}/versions",json=revision).json()
    assert client.post(f'/api/tasks/{tid}/triage').json()['state']=='blocked'
    assert next(h for h in client.post('/api/context/query',json=query).json() if h['source_id']==memory['id'])['decision_status']=='BLOCK'
    lock(client,reviewer,plan,nv)
    assert client.post(f'/api/tasks/{tid}/triage').json()['state']=='blocked' # fresh lock is not challenge
    client.post(f"/api/results/{result['id']}/challenge",json={'reason':'New context, new challenge'})
    process_job_api(client)
    assert client.post(f'/api/tasks/{tid}/triage').json()['state']=='approval_required' # old approval not reused


def test_plan_audit_failure_rolls_back(client,reviewer,settings):
    """PLAN-008 | transaction failure | real SQLite trigger | audit insert abort | no half-created PLAN/version."""
    p,e=seed(client,reviewer);tid=task(client,p,e)
    with sqlite3.connect(settings.db_path) as db:
        db.execute("CREATE TRIGGER fail_plan BEFORE INSERT ON records WHEN NEW.kind='audit' AND json_extract(NEW.body,'$.event')='plan.version_created' BEGIN SELECT RAISE(ABORT,'isolated plan audit fault'); END")
    with pytest.raises(sqlite3.IntegrityError):
        client.post('/api/plans',json={'task_id':tid,'title':'Rollback test','resources':[{'kind':'evidence','id':e['id']}]})
    assert client.get('/api/plans').json()==[]
    with sqlite3.connect(settings.db_path) as db:
        assert db.execute("SELECT count(*) FROM records WHERE kind='plan_version'").fetchone()[0]==0


def test_ai_cannot_bypass_plan_and_archive_context(ai):
    """PLAN-009 | real HTTP transport | bound archive context | no lock/extra refs/revoke | blocked; current exact lock sends actual selected text only."""
    c,r,body,pol,seen,output,settings,_=ai
    p=c.get('/api/projects').json()[0]
    a=c.post('/api/archive',json={'project_id':p['id'],'relative_path':'selected.txt','content':'Synthetic chosen archive context'}).json()
    plan,v,_=make(c,r,tid=body['task_id'],resources=[{'kind':'archive','id':a['id']}])
    assert c.post('/api/ai/requests',json=body).json()['detail']=='PLAN_CONTEXT_NOT_CURRENT'
    l=lock(c,r,plan,v);body['plan_lock_id']=l['id']
    c.post('/api/ai/policy',headers=r,json=pol)
    req=c.post('/api/ai/requests',json=body).json()
    assert req['effective_classification']=='CONFIDENTIAL' and a['id'] in req['context']
    run=lambda key:c.post(f"/api/ai/requests/{key['id']}/run",headers=r,json={'context_hash':key['context_hash'],'reason':'Explicit isolated transport'}).json()
    assert run(req)['attempt']['state']=='DRAFT_UNCHALLENGED' and len(seen)==1
    assert 'Synthetic chosen archive context' in seen[0][1]['messages'][0]['content']
    req=c.post('/api/ai/requests',json=body).json()
    body['evidence_ids']=[c.get('/api/evidence').json()[0]['id']]
    assert c.post('/api/ai/requests',json=body).json()['detail']=='PLAN_CONTEXT_MUST_NOT_BE_OVERRIDDEN'
    c.post(f"/api/plan-locks/{l['id']}/revoke",headers=r,json={'reason':'Stop queued context use'})
    assert run(req)['attempt']['reason']=='PLAN_CONTEXT_NOT_CURRENT' and len(seen)==1


def test_ai_plan_bounds_secrets_and_late_creation(ai):
    """PLAN-010 | prepared request before PLAN, 9 sources, locked secret | real API | fail closed without any transport."""
    c,r,body,pol,seen,output,settings,_=ai
    p=c.get('/api/projects').json()[0]
    c.post('/api/ai/policy',headers=r,json=pol)
    queued=c.post('/api/ai/requests',json=body).json()
    resources=[]
    for i in range(9):
        m=c.post('/api/memory',json={'project_id':p['id'],'task_id':body['task_id'],'category':'inference','content':f'Isolated context {i}','evidence_ids':[]}).json()
        resources.append({'kind':'memory','id':m['id']})
    plan,v,original=make(c,r,tid=body['task_id'],resources=resources);l=lock(c,r,plan,v)
    blocked=c.post(f"/api/ai/requests/{queued['id']}/run",headers=r,json={'context_hash':queued['context_hash'],'reason':'Late PLAN must block old request'}).json()
    assert blocked['attempt']['reason']=='PLAN_CONTEXT_NOT_CURRENT' and seen==[]
    body['plan_lock_id']=l['id']
    assert c.post('/api/ai/requests',json=body).json()['detail']=='CONTEXT_COUNT_EXCEEDED'
    a=c.post('/api/archive',json={'project_id':p['id'],'relative_path':'secret-test.txt','content':'password=not_a_real_secret_test'}).json()
    revision={'expected_version_id':v['id'],'title':'Secret detector case','resources':[{'kind':'archive','id':a['id']}]}
    nv=c.post(f"/api/plans/{plan['id']}/versions",json=revision).json();body['plan_lock_id']=lock(c,r,plan,nv)['id']
    assert c.post('/api/ai/requests',json=body).json()['detail']=='SECRET_PATTERN_BLOCKED' and seen==[]
    body['task_id']=task(c,p,c.get('/api/evidence').json()[0])
    assert c.post('/api/ai/requests',json=body).json()['detail']=='PLAN_CONTEXT_NOT_CURRENT'


def test_ai_plan_request_integrity_fault(ai):
    """PLAN-011 | isolated SQLite corruption | alter saved context after consent hash | no real HTTP transport."""
    c,r,body,pol,seen,output,settings,_=ai
    c.post('/api/ai/policy',headers=r,json=pol)
    req=c.post('/api/ai/requests',json=body).json()
    with sqlite3.connect(settings.db_path) as db:
        value=json.loads(db.execute('SELECT body FROM records WHERE id=?',(req['id'],)).fetchone()[0])
        value['context']='Unexpected corrupted context'
        db.execute('UPDATE records SET body=? WHERE id=?',(json.dumps(value),req['id']))
    response=c.post(f"/api/ai/requests/{req['id']}/run",headers=r,json={'context_hash':req['context_hash'],'reason':'Old exact consent'}).json()
    assert response['attempt']['reason']=='CONTEXT_INTEGRITY_MISMATCH' and seen==[]


@pytest.mark.parametrize('fault',['source_hash','dependency_hash','foreign_dependency'])
def test_plan_integrity_dependency_faults(client,reviewer,settings,fault):
    """PLAN-012 | isolated persisted-record faults | corrupt source/hash/dependency scope | real SQLite/API | 503/422 and no partial PLAN."""
    p,e=seed(client,reviewer);tid=task(client,p,e)
    m=client.post('/api/memory',json={'project_id':p['id'],'category':'inference','content':'Synthetic fault target','evidence_ids':[e['id']]}).json()
    target=m if fault=='source_hash' else e
    with sqlite3.connect(settings.db_path) as db:
        value=json.loads(db.execute('SELECT body FROM records WHERE id=?',(target['id'],)).fetchone()[0])
        if fault=='foreign_dependency': value['project_id']='another-project'
        else: value['content']='Corrupted stored bytes'
        db.execute('UPDATE records SET body=? WHERE id=?',(json.dumps(value),target['id']))
    response=client.post('/api/plans',json={'task_id':tid,'title':'Fault test','resources':[{'kind':'memory','id':m['id']}]})
    assert response.status_code==(422 if fault=='foreign_dependency' else 503)
    assert client.get('/api/plans').json()==[]


def test_plan_byte_budget(client,reviewer):
    """PLAN-013 | actual UTF-8 archive blobs | 9 x128KiB | 1MiB source cap blocks without truncation."""
    p,e=seed(client,reviewer);tid=task(client,p,e)
    refs=[]
    for i in range(9):
        a=client.post('/api/archive',json={'project_id':p['id'],'relative_path':f'bounded-{i}.txt','content':'ä'*65536}).json()
        refs.append({'kind':'archive','id':a['id']})
    assert client.post('/api/plans',json={'task_id':tid,'title':'Bounded source test','resources':refs}).status_code==413
    assert client.get('/api/plans').json()==[]


@pytest.mark.parametrize('boundary',['count','combined_bytes'])
def test_plan_dependency_budgets(client,reviewer,boundary):
    """PLAN-014 | actual Evidence/Memory/archive API records | 65 dependencies or >1MiB combined | fail413, no truncation/partial PLAN."""
    p,e=seed(client,reviewer);tid=task(client,p,e)
    ids=[]
    for i in range(65 if boundary=='count' else 7):
        body={k:e[k] for k in ['project_id','claim','source_url','observed_at','source_type','provider','extraction_method','confidence']}
        body['content']=f'Synthetic dependency {i}' if boundary=='count' else 'x'*20000
        response=client.post('/api/evidence',json=body)
        assert response.status_code==201
        ids.append(response.json()['id'])
    refs=[]
    for start in range(0,len(ids),50):
        m=client.post('/api/memory',json={'project_id':p['id'],'category':'inference','content':'Synthetic dependency budget','evidence_ids':ids[start:start+50]}).json()
        refs.append({'kind':'memory','id':m['id']})
    if boundary=='combined_bytes':
        for i in range(7):
            a=client.post('/api/archive',json={'project_id':p['id'],'relative_path':f'dependency-budget-{i}.txt','content':'ä'*65536}).json()
            refs.append({'kind':'archive','id':a['id']})
    response=client.post('/api/plans',json={'task_id':tid,'title':'Bounded dependency test','resources':refs})
    assert response.status_code==413
    assert ('dependencies exceed' if boundary=='count' else 'content and dependencies exceed') in response.json()['detail']
    assert client.get('/api/plans').json()==[]


def test_plan_concurrent_optimistic_append(client,reviewer):
    """PLAN-015 | real concurrent API/SQLite transactions | two writers same expected version | exactly one201/one409, no lost update."""
    from concurrent.futures import ThreadPoolExecutor
    plan,v,body=make(client,reviewer)
    revision={k:value for k,value in body.items() if k!='task_id'}
    revision['expected_version_id']=v['id']
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses=list(pool.map(lambda _:client.post(f"/api/plans/{plan['id']}/versions",json=revision),range(2)))
    assert sorted(r.status_code for r in responses)==[201,409]
    versions=client.get(f"/api/plans/{plan['id']}/versions").json()
    assert [version['version'] for version in versions]==[2,1]
