"""AXM structure builder MVP contract tests: versioned models, validation, deterministic CALCULATED generation."""
from fastapi.testclient import TestClient
from app.main import create_app


def node(local_id, kind='page', name=None, permissions=None, note=''):
    return {'local_id': local_id, 'kind': kind, 'name': name or local_id.replace('-', ' ').title(),
            'permissions': permissions or [], 'note': note}


def edge(source, target, kind='contains'):
    return {'source': source, 'target': target, 'kind': kind}


def model(nodes, edges=None, **extra):
    return {'nodes': nodes, 'edges': edges or [], 'note': 'Synthetic fixture model', **extra}


def create_structure(client, name='Fixture site', nodes=None, edges=None):
    response = client.post('/api/structures', json=model(nodes or [node('home')], edges,
                                                         name=name, description='Synthetic structure fixture'))
    assert response.status_code == 201, response.text
    return response.json()


def test_structure_creation_roles_and_validation(client, reviewer, settings):
    """STR-001: structures are operator-created; anonymous and reviewer refused; initial version 1 with manifest persisted."""
    anonymous = TestClient(create_app(settings))
    assert anonymous.post('/api/structures', json=model([node('home')], name='Anon attempt')).status_code == 401
    assert client.post('/api/structures', headers=reviewer,
                       json=model([node('home')], name='Reviewer attempt')).status_code == 403
    assert client.post('/api/structures', json=model([node('home')], name='')).status_code == 422
    structure = create_structure(client, nodes=[node('home', name='Start'), node('about', name='Über Uns')],
                                 edges=[edge('home', 'about')])
    assert structure['version'] == 1 and structure['state'] == 'active'
    assert structure['name'] == 'Fixture site'
    assert client.post('/api/structures', json=model([node('a', name='Eins'), node('b', name='Zwei')],
                                                     name='TwoRoots')).status_code == 422
    versions = client.get(f"/api/structures/{structure['id']}/versions").json()
    assert len(versions) == 1 and versions[0]['version'] == 1 and versions[0]['predecessor_id'] is None
    assert len(versions[0]['manifest_hash']) == 64
    assert versions[0]['created_by'] == 'operator'


def test_structure_model_validation_rejects_invalid_graphs(client):
    """STR-002: duplicate ids, unknown/self endpoints, non-container parents, cycles, double parents, bounds, slugs, route collisions."""
    assert client.post('/api/structures', json=model([node('a'), node('a')], name='Dup')).status_code == 422
    assert client.post('/api/structures', json=model([node('a')], [edge('a', 'missing')], name='Unknown')).status_code == 422
    assert client.post('/api/structures', json=model([node('a')], [edge('a', 'a')], name='Self')).status_code == 422
    assert client.post('/api/structures', json=model([node('c', 'component'), node('x')],
                                                  [edge('c', 'x')], name='Comp')).status_code == 422
    assert client.post('/api/structures', json=model([node('a'), node('b'), node('c')],
                                                  [edge('a', 'b'), edge('b', 'c'), edge('c', 'a')], name='Cycle')).status_code == 422
    assert client.post('/api/structures', json=model([node('a'), node('b'), node('c', 'section'), node('d')],
                                                  [edge('a', 'b'), edge('c', 'b'), edge('c', 'd')],
                                                  name='Parents')).status_code == 422
    assert client.post('/api/structures', json=model([node(f'n{i}') for i in range(65)], name='Big')).status_code == 422
    assert client.post('/api/structures', json=model([node('a', name='!!!')], name='Slug')).status_code == 422
    assert client.post('/api/structures', json=model([node('Bad Id')], name='LocalId')).status_code == 422
    assert client.post('/api/structures', json=model([node('home'), node('x', name='Katalog'),
                                                      node('y', name='katalog!')],
                                                  [edge('home', 'x'), edge('home', 'y')],
                                                  name='Routes')).status_code == 422


def test_structure_versions_append_only_and_identical_rejected(client, reviewer):
    """STR-003: versions chain via predecessor and stay immutable; identical manifests rejected 409; reviewer refused."""
    structure = create_structure(client, nodes=[node('home', name='Start')])
    assert client.post(f"/api/structures/{structure['id']}/versions",
                       headers=reviewer, json=model([node('home', name='Anderes')])).status_code == 403
    second = client.post(f"/api/structures/{structure['id']}/versions",
                         json=model([node('home', name='Start'), node('contact', name='Kontakt')],
                                    [edge('home', 'contact')]))
    assert second.status_code == 201 and second.json()['version'] == 2
    assert second.json()['predecessor_id'] is not None
    assert client.get(f"/api/structures/{structure['id']}").json()['version'] == 2
    identical = client.post(f"/api/structures/{structure['id']}/versions",
                            json=model([node('home', name='Start'), node('contact', name='Kontakt')],
                                       [edge('home', 'contact')]))
    assert identical.status_code == 409
    history = client.get(f"/api/structures/{structure['id']}/versions").json()
    assert [v['version'] for v in history] == [2, 1]
    assert history[1]['nodes'] == [node('home', name='Start')]  # immutable history stays unchanged


def test_generation_routes_and_skeleton_deterministic(client):
    """STR-004: routing overview follows the page containment forest; skeleton carries empty placeholders and relations."""
    nodes = [node('home', name='Startseite'), node('shop', name='Shop'),
             node('catalogue', 'section', name='Katalog'), node('card', 'component', name='Artikelkarte'),
             node('buy', 'action', name='In den Warenkorb'), node('feed', 'data', name='Preise')]
    edges = [edge('home', 'shop'), edge('shop', 'catalogue'), edge('catalogue', 'card'),
             edge('card', 'buy', 'triggers'), edge('catalogue', 'feed', 'depends_on')]
    structure = create_structure(client, nodes=nodes, edges=edges)
    generated = client.get(f"/api/structures/{structure['id']}/generate").json()
    assert generated['result_class'] == 'CALCULATED' and generated['prediction'] == 'NONE'
    assert generated['basis'] == 'STRUCTURE_VERSION_MANIFEST'
    assert [route['path'] for route in generated['routes']] == ['/', '/shop']
    assert generated['routes'][1]['title'] == 'Shop' and generated['routes'][1]['node'] == 'shop'
    roots = {root['local_id']: root for root in generated['ui_skeleton']['roots']}
    assert set(roots) == {'home', 'buy', 'feed'}  # non-contained nodes become skeleton roots
    shop = roots['home']['children'][0]
    catalogue = shop['children'][0]
    card = catalogue['children'][0]
    assert card['placeholder'] == 'EMPTY' and card['title'] == 'Artikelkarte'
    assert roots['buy']['relations'] == [{'from': 'card', 'kind': 'triggers'}]
    assert roots['feed']['relations'] == [{'from': 'catalogue', 'kind': 'depends_on'}]
    assert roots['home']['relations'] == [] and roots['home']['permissions'] == []
    assert 'not enforced authorization' in generated['limits']
    repeat = client.get(f"/api/structures/{structure['id']}/generate").json()
    assert repeat == generated  # deterministic, no hidden state


def test_generation_is_version_pinned(client):
    """STR-005: generation references one stored version; old versions keep their original routes; unknown version 404."""
    structure = create_structure(client, nodes=[node('home', name='Start')])
    client.post(f"/api/structures/{structure['id']}/versions",
                json=model([node('home', name='Start'), node('imprint', name='Impressum')],
                           [edge('home', 'imprint')]))
    latest = client.get(f"/api/structures/{structure['id']}/generate").json()
    assert [route['path'] for route in latest['routes']] == ['/', '/impressum'] and latest['version'] == 2
    pinned = client.get(f"/api/structures/{structure['id']}/generate", params={'version': 1}).json()
    assert [route['path'] for route in pinned['routes']] == ['/'] and pinned['version'] == 1
    assert pinned['manifest_hash'] != latest['manifest_hash']
    assert client.get(f"/api/structures/{structure['id']}/generate", params={'version': 9}).status_code == 404


def test_structure_deactivation_confirmed_and_retained(client, reviewer):
    """STR-006: reviewer-confirmed deactivation retains all versions; operator refused; unconfirmed 422; repeat 409."""
    structure = create_structure(client, nodes=[node('home')])
    assert client.post(f"/api/structures/{structure['id']}/deactivate",
                       json={'confirm': True, 'reason': 'operator attempt'}).status_code == 403
    assert client.post(f"/api/structures/{structure['id']}/deactivate", headers=reviewer,
                       json={'confirm': False, 'reason': 'unconfirmed attempt'}).status_code == 422
    assert client.post(f"/api/structures/{structure['id']}/deactivate", headers=reviewer,
                       json={'confirm': True, 'reason': 'kurz'}).status_code == 422
    assert client.post(f"/api/structures/{structure['id']}/deactivate", headers=reviewer,
                       json={'confirm': True, 'reason': 'Explicit fixture deactivation'}).status_code == 200
    assert client.get(f"/api/structures/{structure['id']}").json()['state'] == 'deactivated'
    assert len(client.get(f"/api/structures/{structure['id']}/versions").json()) == 1  # retained
    assert client.post(f"/api/structures/{structure['id']}/versions", json=model([node('home')])).status_code == 409
    assert client.post(f"/api/structures/{structure['id']}/deactivate", headers=reviewer,
                       json={'confirm': True, 'reason': 'second attempt'}).status_code == 409


def test_structure_stop_blocks_mutations_not_reads(client, reviewer):
    """STR-007: the emergency stop blocks creation, versioning and deactivation; reads and generation stay available."""
    structure = create_structure(client, nodes=[node('home')])
    client.post('/api/control/stop', headers=reviewer, json={'active': True, 'reason': 'Isolated stop'})
    try:
        assert client.post('/api/structures', json=model([node('x')], name='Blocked')).status_code == 409
        assert client.post(f"/api/structures/{structure['id']}/versions",
                           json=model([node('home'), node('new')])).status_code == 409
        assert client.post(f"/api/structures/{structure['id']}/deactivate", headers=reviewer,
                           json={'confirm': True, 'reason': 'stop is active'}).status_code == 409
        assert client.get(f"/api/structures/{structure['id']}/generate").json()['result_class'] == 'CALCULATED'
        assert client.get('/api/structures').json()[0]['id'] == structure['id']
    finally:
        client.post('/api/control/stop', headers=reviewer, json={'active': False, 'reason': 'Isolated reset'})


def test_structure_permissions_are_declared_metadata(client):
    """STR-008: node permissions are stored and reproduced as declared metadata, not enforced authorization; bounds held."""
    structure = create_structure(client, nodes=[node('admin', name='Admin', permissions=['reviewer', 'operator'])])
    version = client.get(f"/api/structures/{structure['id']}/versions").json()[0]
    assert version['nodes'][0]['permissions'] == ['reviewer', 'operator']
    skeleton = client.get(f"/api/structures/{structure['id']}/generate").json()['ui_skeleton']['roots'][0]
    assert skeleton['permissions'] == ['reviewer', 'operator']
    assert client.post('/api/structures', json=model([node('x', permissions=['a' * 65])], name='Perm')).status_code == 422
    assert client.post('/api/structures', json=model([node('x', permissions=[f'p{i}' for i in range(9)])],
                                                      name='Perm9')).status_code == 422


def test_structure_slug_normalization_and_nested_paths(client):
    """STR-009: page names become deterministic URL segments (umlauts, spaces, punctuation); nested pages nest paths."""
    nodes = [node('root', name='Wurzel Seite!'), node('child', name='Konto & Einstellungen'),
             node('grand', name='grand child')]
    structure = create_structure(client, nodes=nodes, edges=[edge('root', 'child'), edge('child', 'grand')])
    routes = client.get(f"/api/structures/{structure['id']}/generate").json()['routes']
    assert [route['path'] for route in routes] == ['/', '/konto-einstellungen', '/konto-einstellungen/grand-child']


def test_structure_pages_below_sections_stay_in_skeleton(client):
    """STR-010: a page nested under a section contributes to the skeleton, not to routing; unknown ids 404."""
    nodes = [node('home', name='Start'), node('area', 'section', name='Bereich'), node('sub', 'page', name='Unter')]
    structure = create_structure(client, nodes=nodes, edges=[edge('home', 'area'), edge('area', 'sub')])
    generated = client.get(f"/api/structures/{structure['id']}/generate").json()
    assert [route['path'] for route in generated['routes']] == ['/']
    home = generated['ui_skeleton']['roots'][0]
    assert home['children'][0]['children'][0]['local_id'] == 'sub'
    assert client.get('/api/structures/missing/generate').status_code == 404
    assert client.get('/api/structures/missing').status_code == 404
