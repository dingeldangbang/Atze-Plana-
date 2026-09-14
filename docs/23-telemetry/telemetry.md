# Telemetrie — echte ingestete Messreihen, deklarative Geräteregistry

Stand 2026-09-14, Baseline 169 ausgeführte Tests PASS vor dieser Änderung; dieses Inkrement ergänzt 14 Tests (183 PASS). Messwerte existieren ausschließlich, wenn ein Device sie tatsächlich über HTTP eingereicht hat. Keine erfundenen Sensorwerte, keine Hardwarefähigkeitsbehauptung.

## Zweck / explizite Non-Goals
Reale deklarative Device-/Sensor-Registry (Operator) und HTTP-Ingistierung (POST /api/telemetry/ingest) mit unveränderlichen, versionierten, hash-verifizierten Messbatches. **Kein WS/MQTT/Serial-Transport (NOT IMPLEMENTED), keine Geräteautodiscovery, keine Kalibrierung, kein Firmware-Upload, keine Sensorzustands-/Gesundheitsbehauptung, keine physikalische Wahrheitsverifikation der Werte, kein Löschen von Messhistorie.** Werte sind vom Device erklärt (SUBMITTED), nie als verifizierte physikalische Messung dargestellt.

## Konfiguration / Rollen
`ATZE_TELEMETRY_TOKEN` (siehe [Konfiguration](../19-operations/configuration.md)): optionales, getrenntes Device-Fleet-Bearer, ≥32 Zeichen, von allen Plattform-Credentials verschieden. Leer/fehlend = Ingest fail-closed gesperrt (403 NOT CONFIGURED); Registry und Lesezugriffe bleiben Plattform-Rollen vorbehalten. **Bekannte Single-Credential-Grenze:** ein geteiltes Fleet-Token identifiziert kein einzelnes Gerät; die Device-Zuordnung folgt aus der Sensor-Registry der Batch-Payload, nicht aus dem Token. Geräteidentitäten sind deklarativ (Owner-Angabe), keine kryptografische Geräteauthentifizierung.

Rollen: Operator registriert Devices/Sensoren (+); Reviewer deaktiviert einzeln mit expliziter Bestätigung und Begründung (−); Device-Token ingiest; Operator/Reviewer lesen. Not-Stop blockt alle Telemetrie-Mutationen (409), Lesezugriffe bleiben.

## API-Vertrag
| Route | Rolle | Wirkung | Fehler |
|---|---|---|---|
| POST /api/telemetry/devices | operator | Device deklarieren + Audit | 409 Name doppelt |
| GET /api/telemetry/devices | both | Registry lesen (keine Erreichbarkeitsaussage) | — |
| POST /api/telemetry/devices/{id}/sensors | operator | Sensor deklarieren + Audit | 404 Device, 409 deaktiviert/Name doppelt |
| GET /api/telemetry/devices/{id}/sensors | both | Sensoren lesen | 404 Device |
| POST /api/telemetry/ingest | device | Unveränderlicher Batch-Blob + Metadaten + Audit | 401/403 Token, 404 Sensor, 409 deaktiviert/Stop, 422 Validierung |
| GET /api/telemetry/batches | both | Batch-Metadaten (optional device_id-Filter) | 404 Filter-Device |
| GET /api/telemetry/batches/{id}/samples | both | Hash-/Größenverifizierter Blob-Read | 503 korrupt |
| POST /api/telemetry/devices/{id}/deactivate | reviewer | Bestätigte Deaktivierung + Audit, Daten bleiben | 409 erneut, 422 confirm/reason |
| POST /api/telemetry/sensors/{id}/deactivate | reviewer | Bestätigte Deaktivierung + Audit, Daten bleiben | 409 erneut, 422 confirm/reason |

## Daten-/Wire-Vertrag
Sensorkategorien: voltage, current, rpm, temperature, imu, throttle, steering, speed, custom. Sensor: Name (pro Device eindeutig), optionales `declared_range` (min<max, **Owner-Aussage, keine Kalibrierung**), `identification` IDENTIFIED|UNKNOWN. Sample: `sensor_id`, endlicher Wert (NaN/Infinity → 422), `timestamp` zwingend ISO-8601 **mit** UTC-Offset (Geräteuhr als deklariert gespeichert, keine Plausibilitätskorrektur), `quality` ok|suspect (**Device-Selbstauskunft**, keine Servergesundheitsprüfung). Batch: 1–1000 Samples, alle Sensoren genau eines Devices, optionale session/conditions (Freitext).

Speicherung: Samples als kanonisches JSON (sort_keys, kompakt) über den bestehenden Storage-Tier (auto, O_EXCL+fsync+Verifikation), sha256 + size_bytes + Tier + interner UUID-Key im Metadaten-Record; `first_timestamp`/`last_timestamp` aus geparsten Zeitstempeln; `flagged_out_of_range` (gegen declared_range) und `suspect_samples` als Zähler, kein automatischer Verwurf. Batches sind unveränderlich (kein Update/Delete-Endpunkt). Lesen verifiziert Hash und Größe; Abweichung → 503, Metadaten bleiben beweisbar erhalten.

## Deaktivierung (−) / Entfernen
Nur Reviewer mit `confirm: true` und Begründung; erneut Deaktivieren → 409. Deaktiviertes Device/Sensor blockt weiteren Ingest und neue Sensordeklaration (409); alle Bestände und Historie bleiben vollständig lesbar. Es existiert bewusst kein Datenlösch-Endpunkt für Messhistorie.

## Transaktionen / Fehler / Recovery
Ingest prüft Stop (guard) vor Schreibung; Metadaten-Record und Blob werden vor Audit-Commit persistiert. Unterbrochene Schreibvorgänge hinterlassen entweder verifizierbaren Batch oder nichts — kein Teilzustand als Erfolg. Fehlende Token-Konfiguration ist kein Fehlerzustand, sondern der sichere Default. 422-Antworten serialisieren nicht-endliche Floats als String (kein Render-Crash), die Schema-Ablehnung bleibt erhalten.

## Validierung / Grenzen
14 neue Tests ([Testkatalog](../14-testing/test-catalog.md)): Token-Trennung und Fail-closed (403/401), Settings-Validierung, 422-Fälle (Kind, Range, NaN, naive/ungültige Zeitstempel, >1000, Cross-Device-Batch), Out-of-Range-/Suspect-Flagging, Hash-Verifikation, Blob-Korruption → 503, Stop-Block mit Freigabe, Reviewer-Deaktivierung inkl. 409 und Datenerhalt, Audit-Kette. **Nicht validiert (NOT RUN):** physische ESP32-/Sensormessung, echte Geräteurhen, WS/MQTT/Serial-Transport, Zeitplausibilität von Geräteuhren, Per-Device-Rate-Limits. Dieses Modul ist kein Beweis für Hardwarefunktion; Telemetrie-Devices im Registry sind deklarierte Identitäten, keine verbundenen Geräte ([Roadmap](../00-overview/roadmap.md)).
