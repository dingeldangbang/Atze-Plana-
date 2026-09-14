"""Harness integrity tests do not simulate successful model inference."""
import hashlib
import json
from pathlib import Path
import pytest
from scripts.validate_local_model import run, verify, require


def test_local_model_requires_opt_in(tmp_path):
    """LM-001 | opt-in gate | previous PASS report | run without consent | overwritten BLOCKED before I/O, no model success."""
    report=tmp_path/'report.json';report.write_text('{"status":"PASS"}')
    with pytest.raises(RuntimeError,match='allow-fixtures'):
        run(tmp_path/'no-model',tmp_path/'no-runtime',report)
    assert json.loads(report.read_text())['status']=='BLOCKED'


def test_local_model_missing_artifacts(tmp_path):
    """LM-002 | real missing file | opt-in | preflight | BLOCKED, not simulated success."""
    report=tmp_path/'report.json'
    with pytest.raises(RuntimeError,match='missing'):
        run(tmp_path/'missing-model',tmp_path/'missing-runtime',report,allow_fixtures=True)
    assert json.loads(report.read_text())['status']=='BLOCKED'


def test_local_model_artifact_hash(tmp_path):
    """LM-003 | byte integrity helper | explicitly synthetic small file | size/hash/symlink checks | genuine hash checks, NOT model proof."""
    p=tmp_path/'synthetic';p.write_bytes(b'synthetic-integrity-input')
    expected={'size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
    assert verify(p,expected)==expected['sha256']
    with pytest.raises(RuntimeError,match='size'):verify(p,{**expected,'size':1})
    with pytest.raises(RuntimeError,match='SHA256'):verify(p,{**expected,'sha256':'0'*64})
    link=tmp_path/'link';link.symlink_to(p)
    with pytest.raises(RuntimeError,match='symlink'):verify(link,expected)
