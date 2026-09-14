"""Trend query API: read-only deterministic analysis of immutable submitted samples; no side effects, no prediction."""
from fastapi import Depends
from app.trend_models import CheckCatalog, TrendQueryInput, TrendReport
from app.trend_service import analyze_sensor, catalog


def register_trend_api(app, actor, connection, storage):
    db_dependency = Depends(connection, scope='function')

    @app.post('/api/telemetry/trends', response_model=TrendReport, tags=['telemetry'],
              openapi_extra={'x-role': 'both', 'x-side-effects': 'None; deterministic read-only analysis of immutable submitted samples; recomputed per query, no persistence, no prediction, no physical truth claim'})
    def analyze(body: TrendQueryInput, who=Depends(actor), db=db_dependency):
        return analyze_sensor(db, storage, body.sensor_id, body.session)

    @app.get('/api/telemetry/trends/checks', response_model=CheckCatalog, tags=['telemetry'],
             openapi_extra={'x-role': 'both', 'x-side-effects': 'None; static criteria catalog'})
    def checks(who=Depends(actor)):
        return catalog()
