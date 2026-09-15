"""Structure validation and deterministic generation: append-only versions, CALCULATED outputs, no invention."""
import hashlib
import json
import re
from types import SimpleNamespace

from fastapi import HTTPException

from app.structure_models import MAX_EDGES, MAX_NODES, EdgeKind, NodeKind

CONTAINERS = {'page', 'section'}  # only pages and sections may contain other nodes


def stored_model(record: dict) -> tuple:
    """Attribute view of a stored version body for reuse by generation and comparison."""
    return ([SimpleNamespace(**item) for item in record['nodes']],
            [SimpleNamespace(**item) for item in record['edges']])


def compare_versions(from_record: dict, to_record: dict) -> dict:
    """Deterministic directional diff of two stored version manifests; CALCULATED review aid, never a merge/repair."""
    from_nodes = {item['local_id']: item for item in from_record['nodes']}
    to_nodes = {item['local_id']: item for item in to_record['nodes']}
    node_fields = ('kind', 'name', 'permissions', 'note')
    nodes = {'added': sorted(set(to_nodes) - set(from_nodes)),
             'removed': sorted(set(from_nodes) - set(to_nodes)),
             'changed': []}
    for local_id in sorted(set(from_nodes) & set(to_nodes)):
        before, after = from_nodes[local_id], to_nodes[local_id]
        changes = {field: {'from': before[field], 'to': after[field]}
                   for field in node_fields if before[field] != after[field]}
        if changes:
            nodes['changed'].append({'local_id': local_id, 'changes': changes})

    def key(item):
        return (item['source'], item['target'], item['kind'])
    from_edges = {key(item) for item in from_record['edges']}
    to_edges = {key(item) for item in to_record['edges']}
    edges = {'added': [list(item) for item in sorted(to_edges - from_edges)],
             'removed': [list(item) for item in sorted(from_edges - to_edges)]}

    from_routes = {route['path']: route for route in generate_routes(*stored_model(from_record))}
    to_routes = {route['path']: route for route in generate_routes(*stored_model(to_record))}
    routes = {'added': sorted(set(to_routes) - set(from_routes)),
              'removed': sorted(set(from_routes) - set(to_routes)),
              'changed': [{'path': path, 'title': {'from': from_routes[path]['title'], 'to': to_routes[path]['title']}}
                          for path in sorted(set(from_routes) & set(to_routes))
                          if from_routes[path]['title'] != to_routes[path]['title']]}
    return {'identical': from_record['manifest_hash'] == to_record['manifest_hash'],
            'nodes': nodes, 'edges': edges, 'route_changes': routes}


def slug(name: str) -> str:
    """Deterministic URL segment: lowercase ASCII, non-alphanumeric runs collapse to one hyphen."""
    normalized = re.sub(r'[^a-z0-9]+', '-', name.lower().replace('ä', 'ae').replace('ö', 'oe')
                        .replace('ü', 'ue').replace('ß', 'ss')).strip('-')
    return normalized


def validate_model(nodes: list, edges: list) -> None:
    """Full structural validation before a version may be persisted; rejects with 422/409, never repairs."""
    if len(nodes) > MAX_NODES or len(edges) > MAX_EDGES:
        raise HTTPException(422, f'Model exceeds the bounds of {MAX_NODES} nodes / {MAX_EDGES} edges')
    local_ids = [node.local_id for node in nodes]
    if len(set(local_ids)) != len(local_ids):
        raise HTTPException(422, 'Node local_id must be unique within a version')
    index = {node.local_id: node for node in nodes}
    parents = {}
    for edge in edges:
        if edge.source == edge.target:
            raise HTTPException(422, 'Edges must not reference the same node on both ends')
        if edge.source not in index or edge.target not in index:
            raise HTTPException(422, 'Edge references an unknown node')
        if edge.kind == 'contains':
            if index[edge.source].kind not in CONTAINERS:
                raise HTTPException(422, f"Only {'/'.join(sorted(CONTAINERS))} nodes may contain other nodes")
            if edge.target in parents:
                raise HTTPException(422, 'A node may have at most one contains-parent')
            parents[edge.target] = edge.source
    # containment must be acyclic (forest)
    for start in parents:
        seen, current = set(), start
        while current in parents:
            if current in seen:
                raise HTTPException(422, 'contains edges must form a forest without cycles')
            seen.add(current)
            current = parents[current]
    for node in nodes:
        if node.kind == 'page' and not slug(node.name):
            raise HTTPException(422, 'Page names must yield a non-empty URL segment')
    root_pages = [node for node in nodes if node.kind == 'page' and node.local_id not in parents]
    if len(root_pages) > 1:
        raise HTTPException(422, 'At most one page may be a root (it occupies the path /); '
                                 'connect further pages below the root page')
    routes = generate_routes(nodes, edges)
    if len({route['path'] for route in routes}) != len(routes):
        raise HTTPException(422, 'Generated route paths must be unique; rename the affected pages')


def generate_routes(nodes: list, edges: list) -> list[dict]:
    """Deterministic routing overview from the containment forest: one path per page node."""
    index = {node.local_id: node for node in nodes}
    parents = {edge.target: edge.source for edge in edges if edge.kind == 'contains'}
    routes = []
    for node in nodes:
        if node.kind != 'page':
            continue
        chain, current = [node], node.local_id
        while current in parents:
            current = parents[current]
            chain.insert(0, index[current])
        if any(ancestor.kind != 'page' for ancestor in chain[:-1]):
            continue  # a page below a section contributes to that page's skeleton, not to routing
        path = '/' + '/'.join(slug(ancestor.name) for ancestor in chain[1:]) if len(chain) > 1 else '/'
        routes.append({'path': path or '/', 'node': node.local_id, 'title': node.name})
    return sorted(routes, key=lambda route: route['path'])


def generate_skeleton(nodes: list, edges: list) -> dict:
    """Deterministic UI placeholder skeleton (CALCULATED) from one structure version; no file is written."""
    index = {node.local_id: node for node in nodes}
    children = {}
    for edge in edges:
        if edge.kind == 'contains':
            children.setdefault(edge.source, []).append(edge.target)
    related = {}
    for edge in edges:
        if edge.kind in ('triggers', 'depends_on'):
            related.setdefault(edge.target, []).append({'from': edge.source, 'kind': edge.kind})

    def subtree(local_id: str) -> dict:
        node = index[local_id]
        value = {'local_id': node.local_id, 'kind': node.kind, 'title': node.name,
                 'placeholder': 'EMPTY', 'permissions': node.permissions,
                 'relations': sorted(related.get(node.local_id, []), key=lambda r: (r['kind'], r['from']))}
        nested = [subtree(child) for child in sorted(children.get(node.local_id, []))]
        if nested:
            value['children'] = nested
        return value

    roots = sorted(node.local_id for node in nodes
                   if not any(edge.kind == 'contains' and edge.target == node.local_id for edge in edges))
    return {'roots': [subtree(root) for root in roots]}


def manifest_hash(nodes: list, edges: list) -> str:
    canonical = json.dumps({'nodes': [node.model_dump() for node in nodes],
                            'edges': [edge.model_dump() for edge in edges]},
                           sort_keys=True, ensure_ascii=False, separators=(',', ':'))
    return hashlib.sha256(canonical.encode()).hexdigest()


def stored_hash(version: dict) -> str:
    canonical = json.dumps({'nodes': version['nodes'], 'edges': version['edges']},
                           sort_keys=True, ensure_ascii=False, separators=(',', ':'))
    return hashlib.sha256(canonical.encode()).hexdigest()
