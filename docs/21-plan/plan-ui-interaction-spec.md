# PLAN — Vollständige UI-, Interaktions-, Code- und Abhängigkeitsspezifikation (verbindliche Vorgabe)

Status: **SPEZIFIKATION (SOLL), kein Implementierungsstatusbericht.** Aufgenommen per Nutzervorgabe am 2026-09-14 als Ergänzung der bestehenden PLAN-Spezifikation ([Context-Lock-Vertrag](context-lock.md)). Die [REALITY_POLICY](../../REALITY_POLICY.md) bleibt übergeordnet: Nichts in diesem Dokument behauptet eine Implementierung; der tatsächliche Stand steht ausschließlich in der [Roadmap/Modulmatrix](../00-overview/roadmap.md) und der [Master-Abnahmematrix](../00-overview/master-acceptance.md).

Bindende Kernregel (Abschnitte 71, 99, 107): Jede sichtbare UI-Funktion benötigt einen realen technischen Pfad (UI → Interaction → Action → Command/Query → Domain Logic → Dependency → Resource → Result → Evidence/Audit → UI State). Reine UI-Darstellung ohne funktionierenden Pfad, Mock-/Demo-Ergebnisse im Betriebsweg, tote Buttons und unbemerkte Fallbacks werden nicht akzeptiert. UI-Funktionen dürfen erst als verfügbar dargestellt werden, wenn Implementierung, Tests und Doku im selben Schnitt vorliegen (Abschnitt 99: sonst NOT COMPLETE).

Umsetzungsreihenfolge (bestätigt): Telemetrie → Trend-Engine → Resource-Manager → MCP tools/call → Agent Builder v1 → Monitoring/Visualisierung. Die Abschnitte 57, 93 und 100–106 (Command Palette, globaler Aktionsraum, Feature-Traceability-Matrix, Action-/Dependency-Registry, UI-Health-Check, End-to-End-Trace) sind verbindliche Abnahmekriterien für jedes künftige UI-Inkrement, insbesondere Modul 6 (Monitoring/Visualisierung) und die Anbindungsverwaltung (Hinzufügen +, bestätigtes Entfernen −).

---

# PLAN – VOLLSTÄNDIGE UI-, INTERAKTIONS-, CODE- UND ABHÄNGIGKEITSSPEZIFIKATION

Der PLAN-Bereich ist ein vollständiges Arbeits-, Planungs-, Kontext-, Workflow- und Ausführungsmodul.

Für **jede Funktion, Aktion und Interaktion** muss eine durchgängige Kette existieren:

```text
UI
 ↓
Interaction
 ↓
Action
 ↓
Command / Application Service
 ↓
Domain Logic
 ↓
Dependency / Adapter
 ↓
Resource / Device / API / Database
 ↓
Result
 ↓
Evidence / Audit
 ↓
UI State
```

Eine reine UI-Darstellung ohne funktionierenden technischen Pfad ist nicht zulässig.

---

# 1. GRUNDPRINZIP

Jede UI-Funktion muss mindestens eindeutig definieren:

```text
FUNCTION_ID
UI_COMPONENT
USER_ACTION
INTERACTION
COMMAND
INPUT
VALIDATION
PERMISSION
DEPENDENCIES
EXECUTION_PATH
RESULT
ERROR STATES
AUDIT EVENT
STATE UPDATE
UI UPDATE
TEST
```

Beispiel:

```text
FUNCTION:
Create Workflow Node

UI:
Workflow Canvas

USER:
Click "Add Node"

ACTION:
CREATE_NODE

INPUT:
Node Type
Name
Position

VALIDATION:
Node Type valid
Plan writable

PERMISSION:
PLAN_EDIT

CODE:
CreateNodeCommand
    ↓
WorkflowService
    ↓
WorkflowRepository

RESULT:
Workflow Node persisted

UI:
Canvas updated

AUDIT:
NODE_CREATED
```

---

# 2. UI-ARCHITEKTUR

PLAN besteht logisch aus:

```text
┌────────────────────────────────────────────────────────────┐
│ PLAN HEADER                                                │
│ Project / Plan / Context Lock / Status / Actions          │
├───────────────┬──────────────────────────────┬─────────────┤
│ NAVIGATION     │ MAIN WORKSPACE               │ INSPECTOR   │
│               │                              │             │
│ Tasks          │ Workflow Canvas             │ Properties  │
│ Resources      │ Tables                      │ Context     │
│ Evidence       │ Documents                   │ Permissions │
│ Devices        │ Timeline                    │ Validation  │
│ Sources        │ 3D                          │ Dependencies│
│ Runs           │ Graph                       │ Audit       │
├───────────────┴──────────────────────────────┴─────────────┤
│ STATUS / EVENTS / VALIDATION / EXECUTION / LOGS            │
└────────────────────────────────────────────────────────────┘
```

---

# 3. GLOBALE UI-BEREICHE

## 3.1 Plan Header

Funktionen:

```text
Plan öffnen
Plan schließen
Plan speichern
Plan umbenennen
Plan duplizieren
Plan archivieren
Plan exportieren
Plan importieren
Plan-Version anzeigen
Context Lock anzeigen
Context Lock öffnen
Context Lock schließen
Plan Status anzeigen
Plan Validation anzeigen
Task-Auswahl
Run starten
Run stoppen
Emergency Stop
```

---

# 4. PLAN HEADER – AKTIONEN

## OPEN_PLAN

```text
UI:
Plan Selector

Interaction:
Click / Search / Enter

Command:
OpenPlanCommand

Dependencies:
PlanRepository
ProjectRepository
PermissionService

Result:
PLAN_OPENED
```

## SAVE_PLAN

```text
Command:
SavePlanCommand

Dependencies:
PlanRepository
VersionService
AuditService

Validation:
Unsaved changes
Schema validity
Conflict state
Permission
```

## DUPLICATE_PLAN

```text
Command:
DuplicatePlanCommand
```

Erzeugt eine neue Plan-Identität und darf keine alten Locks oder Ausführungs-IDs unkontrolliert übernehmen.

## ARCHIVE_PLAN

Benötigt explizite Berechtigung.

```text
ArchivePlanCommand
    ↓
PolicyCheck
    ↓
DependencyCheck
    ↓
Audit
    ↓
Archive
```

---

# 5. PLAN STATUS

Der Header zeigt:

```text
DRAFT
PLANNED
VALIDATED
READY
RUNNING
COMPLETED
FAILED
BLOCKED
```

Zusätzlich:

```text
Context Lock
Challenge Status
Triage Status
Permission Status
Dependency Status
Execution Status
Validation Status
```

Statuswerte müssen aus dem tatsächlichen Systemzustand berechnet werden.

---

# 6. GLOBALER CONTEXT LOCK

Der Plan Header enthält einen permanent sichtbaren Context-Lock-Bereich:

```text
CONTEXT LOCK
● ACTIVE

Context:
PLAN-CTX-00481

Version:
12

Integrity:
VALID

Changes:
0

Conflicts:
0
```

Aktionen:

```text
View Context
Lock
Unlock
Relock
Create Snapshot
Compare Version
Review Changes
Validate Context
```

---

# 7. CONTEXT LOCK – CODEPFAD

```text
LockContextCommand
    ↓
ContextLockService
    ↓
ContextValidator
    ↓
PolicyEngine
    ↓
PermissionService
    ↓
ContextRepository
    ↓
AuditService
```

Für Unlock:

```text
UnlockContextCommand
    ↓
ImpactAnalysis
    ↓
ChallengeService
    ↓
TriageService
    ↓
ApprovalService
    ↓
ContextLockService
```

Ein Unlock darf nicht ausschließlich durch den Frontend-State ausgelöst werden.

---

# 8. TASK NAVIGATION

Linke Navigation:

```text
Tasks
├── All
├── Active
├── Blocked
├── Running
├── Completed
└── Archived
```

Task-Aktionen:

```text
Create
Open
Edit
Duplicate
Move
Group
Ungroup
Rename
Archive
Delete
Lock
Unlock
Assign
Run
Pause
Resume
Cancel
Validate
Compare
```

---

# 9. TASK-DATENMODELL

Jede Task besitzt mindestens:

```text
TaskID
PlanID
TaskVersion
Name
Description
Status
Priority
Owner
Actors
ContextID
WorkflowID
ResourceIDs
EvidenceIDs
DeviceIDs
AgentIDs
PermissionSet
Dependencies
Preconditions
ValidationState
TriagePolicy
ChallengePolicy
CreatedAt
UpdatedAt
```

---

# 10. TASK CREATE

UI:

```text
[+ Task]
```

Dialog:

```text
Name
Description
Type
Priority
Context
Dependencies
Initial Resources
Owner
```

Technischer Pfad:

```text
CreateTaskCommand
    ↓
TaskService
    ↓
TaskValidator
    ↓
TaskRepository
    ↓
AuditService
```

---

# 11. WORKFLOW CANVAS

Das zentrale UI-Modul besitzt:

```text
Canvas
Zoom
Pan
Selection
Multi Selection
Node Creation
Node Editing
Connection Creation
Grouping
Alignment
Auto Layout
Minimap
Search
Filters
History
Undo
Redo
Versioning
Validation Overlay
Execution Overlay
```

---

# 12. CANVAS INTERAKTIONEN

## CLICK

```text
SelectNode
```

## CTRL/CMD + CLICK

```text
ToggleSelection
```

## SHIFT

```text
Range / Multi Selection
```

## DOUBLE CLICK

```text
OpenNodeEditor
```

## DRAG

```text
MoveNode
```

## DRAG CONNECTOR

```text
CreateConnection
```

## RIGHT CLICK

```text
OpenContextMenu
```

## MOUSE WHEEL / TRACKPAD

```text
ZoomCanvas
```

## SPACE + DRAG

```text
PanCanvas
```

## DELETE

```text
DeleteSelection
```

---

# 13. CANVAS COMMANDS

```text
CreateNodeCommand
UpdateNodeCommand
DeleteNodeCommand
MoveNodeCommand
DuplicateNodeCommand
CreateConnectionCommand
DeleteConnectionCommand
GroupNodesCommand
UngroupNodesCommand
AlignNodesCommand
AutoLayoutCommand
CollapseNodeCommand
ExpandNodeCommand
```

Jeder Command muss:

```text
validate()
authorize()
execute()
recordAudit()
emitEvent()
updateState()
```

unterstützen.

---

# 14. WORKFLOW NODE TYPES

Mindestens:

```text
TRIGGER
TASK
CONDITION
AGENT
TOOL
DATA
DEVICE
API
SCRIPT
COMMAND
TEST
VALIDATION
TRIAGE
HUMAN APPROVAL
ACTION
RESULT
DOCUMENTATION
SUBWORKFLOW
END
```

---

# 15. NODE EDITOR

Der Node Inspector besitzt:

```text
General
Inputs
Outputs
Dependencies
Permissions
Preconditions
Timeout
Retry
Evidence
Triage
Challenge
Context
Resources
Agent
Device
Execution
Validation
Audit
Version
```

Änderungen werden nicht direkt unsichtbar gespeichert.

```text
Edit
 ↓
Validate
 ↓
Apply
 ↓
Persist
 ↓
Version
 ↓
Audit
```

---

# 16. NODE PROPERTY TYPES

Unterstützte UI-Eingaben:

```text
Text
Number
Boolean
Enum
Multi Select
Reference
Resource Selector
Device Selector
File Selector
Source Selector
Expression Editor
JSON
YAML
Command Editor
Script Editor
Permission Selector
Policy Editor
```

Jeder Eingabetyp muss client- und serverseitig validiert werden.

---

# 17. RESOURCE PANEL

Ressourcen:

```text
Files
Images
PDF
CAD
Measurements
Datasets
Database Results
Queries
Software
Configurations
Logs
Evidence
Sources
```

Aktionen:

```text
Upload
Import
Add
Remove
Preview
Open
Download
Compare
Version
Hash
Link
Unlink
Attach to Task
Attach to Workflow
Lock
Unlock
Search
Filter
```

---

# 18. RESOURCE-UPLOAD

```text
UI
 ↓
UploadResourceCommand
 ↓
Upload Service
 ↓
Hash Service
 ↓
Virus / Safety Scan
 ↓
Metadata Extraction
 ↓
ResourceRepository
 ↓
Indexing
 ↓
Audit
```

Wichtige IDs:

```text
ResourceID
SHA-256
Version
Source
Owner
CreatedAt
```

---

# 19. RESOURCE DRAG-AND-DROP

Beispiel:

```text
PDF
 ↓ drag
Workflow Node
```

führt aus:

```text
LinkResourceCommand
```

Dabei werden keine Dateien kopiert, wenn nur eine Referenz erforderlich ist.

---

# 20. QUELLEN

Source UI:

```text
URL
Provider
Method
Timestamp
Content Hash
Evidence State
Status
```

Aktionen:

```text
Add Source
Open Source
Refresh
Compare
Create Evidence
Link
Unlink
Lock as Evidence
Challenge
```

Externe Quellen erhalten:

```text
EXTERNAL_SOURCE
```

und müssen provenance-fähig sein.

---

# 21. EVIDENCE

Evidence UI zeigt:

```text
Evidence ID
Type
Source
Timestamp
Hash
Confidence / State
Challenge Result
Triage Result
Used By
```

Status:

```text
VERIFIED
MEASURED
CALCULATED
CONDITIONAL
ESTIMATED
EXTERNAL_SOURCE
CONTRADICTED
UNKNOWN
BLOCKED
NOT RUN
NOT VALIDATED
```

---

# 22. EVIDENCE-AKTIONEN

```text
CreateEvidence
VerifyEvidence
ChallengeEvidence
CompareEvidence
InvalidateEvidence
LinkEvidence
UnlinkEvidence
LockEvidence
ExportEvidence
```

---

# 23. CHALLENGE UI

Challenge Worker wird visuell dargestellt:

```text
PRIMARY RESULT
      ↓
CHALLENGE
 ├── Source
 ├── Consistency
 ├── Alternative
 ├── Causality
 └── Completeness
     ↓
TRIAGE
```

Actions:

```text
Run Challenge
Re-run
Open Findings
Accept
Reject
Escalate
Create Evidence
```

---

# 24. TRIAGE UI

Der Triage Inspector zeigt:

```text
Inputs
Rules
Evidence
Risk
Permissions
Dependencies
Alternatives
Decision
Reason
Confidence / State
```

Beispiel:

```text
Evidence valid       ✓
Permission granted   ✓
Device available     ✓
Risk acceptable      ✓
Dependency ready     ✓

DECISION:
READY
```

oder:

```text
Missing evidence
→ BLOCKED
```

---

# 25. TRIAGE COMMANDS

```text
EvaluateTriageCommand
ReevaluateTriageCommand
OverrideTriageCommand
RejectTriageCommand
EscalateTriageCommand
```

Ein Override muss besonders geschützt und auditierbar sein.

---

# 26. HUMAN APPROVAL

UI:

```text
┌─────────────────────────────┐
│ HUMAN APPROVAL              │
├─────────────────────────────┤
│ Action: Firmware Write      │
│ Device: CT45P-XON #02       │
│ Risk: HIGH                  │
│ Evidence: VALID             │
│                             │
│ [Approve] [Reject]          │
└─────────────────────────────┘
```

Actions:

```text
Approve
Reject
Request Changes
Delegate
Open Evidence
Open Diff
```

---

# 27. PERMISSION UI

Zeigt:

```text
Permission
Scope
Resource
Task
Workflow
Actor
Created
Expires
Revocable
Status
```

Beispiele:

```text
USB READ
BLE READ
NETWORK ACCESS
ADB
FASTBOOT
EDL
FILESYSTEM READ
FILESYSTEM WRITE
TERMINAL
API
MCP TOOL
DEPLOY
```

Keine UI-Berechtigung darf automatisch eine stärkere Backend-Berechtigung erzeugen.

---

# 28. AGENT UI

Agent Inspector:

```text
Agent
Model
Provider
Context
Tools
Permissions
Sandbox
Memory
RAG
Status
Token / Resource Policy
```

Aktionen:

```text
Add Agent
Remove Agent
Configure
Assign
Run
Pause
Stop
Retry
View Logs
View Tool Calls
View Context
View Findings
```

---

# 29. MCP UI

Zeigt reale MCP-Tools:

```text
Tool
Provider
Schema
Arguments
Permissions
Status
Latency
Last Run
Result
```

Actions:

```text
Add Tool
Configure
Enable
Disable
Run
Test
Inspect Schema
Review Permissions
```

Keine als verfügbar angezeigte MCP-Funktion darf lediglich ein Mock sein.

---

# 30. DEVICE UI

Gerätepanel:

```text
Device
Type
Identity
Connection
Firmware
Configuration
Health
Telemetry
Permissions
Last Seen
```

Aktionen:

```text
Discover
Connect
Disconnect
Inspect
Read
Write
Configure
Test
Capture Logs
Collect Evidence
Run Workflow
Repair
```

---

# 31. REAL DEVICE FLOW

```text
UI Action
 ↓
Permission Check
 ↓
Device Adapter
 ↓
Bridge
 ↓
Real Device
 ↓
Response
 ↓
Validation
 ↓
Evidence
 ↓
Audit
 ↓
UI
```

Ein nicht erreichbares Gerät erzeugt:

```text
NOT AVAILABLE
BLOCKED
NOT RUN
```

und niemals einen erfundenen Erfolg.

---

# 32. ANDROID / CT45P

Mögliche Aktionen:

```text
ADB Connect
ADB Shell
Collect Logs
Install APK
Launch App
Capture Screenshot
Read Device Information
Read Firmware Information
Fastboot Detect
Repair Workflow
```

Schreibende bzw. privilegierte Aktionen:

```text
ADB Write
Firmware Flash
EDL Write
Filesystem Write
```

benötigen die entsprechenden Permissions und ggf. Human Approval.

---

# 33. ESP32 / IOT

UI:

```text
Telemetry
Sensor State
Connection
Firmware
Configuration
Health
Calibration
Test Session
```

Aktionen:

```text
Connect
Read Telemetry
Start Test
Stop Test
Calibrate
Upload Firmware
Configure
Export Measurements
Compare Sessions
Replay
```

Torque oder andere physische Messgrößen dürfen nur als real gemessen dargestellt werden.

---

# 34. NETWORK UI

Elemente:

```text
Network Overview
Interfaces
Devices
Connections
Protocols
Traffic
Alerts
Security
```

Aktionen:

```text
Discover
Inspect
Connect
Disconnect
Ping
API Request
SSH
SNMP
MQTT
WebSocket
DNS Lookup
```

Jede Netzwerkaktion ist permission- und policy-gebunden.

---

# 35. FILE / DOCUMENT EDITOR

Unterstützte Interaktionen:

```text
Open
Edit
Save
Rename
Move
Copy
Delete
Version
Compare
Search
Replace
Preview
Link
Attach
```

Änderungen:

```text
Edit
 ↓
Validation
 ↓
Save
 ↓
Hash
 ↓
Version
 ↓
Index
 ↓
Audit
```

---

# 36. DATABASE UI

Funktionen:

```text
Connect
Browse Schema
Search
Query
Explain
Edit
Insert
Update
Delete
Export
Compare
```

Destruktive Operationen:

```text
DELETE
DROP
TRUNCATE
MASS UPDATE
```

müssen separat geschützt werden.

---

# 37. QUERY BUILDER

UI:

```text
Table
Field
Filter
Join
Sort
Group
Limit
Parameters
```

Aktionen:

```text
Add Field
Add Filter
Add Join
Run
Explain
Save Query
Version Query
Attach Query to Task
```

---

# 38. 3D / DIGITAL TWIN UI

Aktionen:

```text
Select Object
Move
Rotate
Zoom
Pan
Inspect
Highlight
Attach Workflow
Show Device
Show Telemetry
Show Errors
Show Dependencies
```

Das 3D-Modell visualisiert reale bzw. ausdrücklich simulierte Zustände.

Simulation muss eindeutig markiert sein.

---

# 39. TIMELINE / REPLAY

Zeigt:

```text
Event
Timestamp
Actor
Agent
Command
Device
Result
Evidence
State Change
```

Interaktionen:

```text
Play
Pause
Stop
Seek
Step
Jump to Event
Filter
Speed
Compare Runs
```

---

# 40. EXECUTION CONTROL

Actions:

```text
Run
Pause
Resume
Cancel
Retry
Stop
Emergency Stop
```

Normal:

```text
Run
 ↓
Preconditions
 ↓
Permission
 ↓
Triage
 ↓
Execution
```

Emergency:

```text
EMERGENCY STOP
 ↓
Revoke Leases
 ↓
Stop Workers
 ↓
Stop Bridge Actions
 ↓
Block Further Execution
 ↓
Audit
```

---

# 41. EXECUTION MONITOR

Live UI:

```text
Queue
Running
Completed
Failed
Blocked
Waiting Approval
```

Pro Task:

```text
Agent
Worker
Device
Runtime
Memory
Network
Progress
Current Action
Logs
```

---

# 42. WORKER MANAGEMENT

Workers können sein:

```text
Local Worker
Temporary Worker
Mobile Worker
Edge Worker
Server Worker
Cloud Worker
Unity Worker
Android Worker
Build Worker
Test Worker
Research Worker
Challenge Worker
```

Actions:

```text
Start
Stop
Restart
Inspect
Logs
Resource Usage
Assign
Release
```

---

# 43. RESOURCE / DEPENDENCY PANEL

Jede Task und jeder Workflow muss seine technischen Abhängigkeiten anzeigen.

```text
DEPENDENCIES

Node
 ├── Service
 ├── Database
 ├── Device
 ├── Agent
 ├── MCP Tool
 ├── File
 ├── Permission
 └── External Provider
```

Status:

```text
AVAILABLE
MISSING
INVALID
BLOCKED
DEGRADED
```

---

# 44. DEPENDENCY GRAPH

Visualisierung:

```text
Task
 ↓
Workflow
 ↓
Agent
 ↓
MCP
 ↓
API
 ↓
Database
```

oder:

```text
Test
 ├── Device
 ├── Sensor
 ├── Firmware
 └── Measurement Dataset
```

Ein fehlender Knoten kann die abhängigen Schritte markieren.

---

# 45. CODE-ARCHITEKTUR

Empfohlene Schichten:

```text
UI
│
├── Components
├── Views
├── State
├── Interaction Layer
└── Client API
        │
        ▼
Application Layer
│
├── Commands
├── Queries
├── Services
├── Policies
└── Orchestration
        │
        ▼
Domain Layer
│
├── Plan
├── Task
├── Workflow
├── Context
├── Evidence
├── Device
├── Agent
├── Permission
└── Execution
        │
        ▼
Infrastructure
│
├── Database
├── Files
├── APIs
├── Device Adapters
├── MCP
├── Workers
├── Network
└── External Providers
```

---

# 46. COMMAND / QUERY TRENNUNG

Mutierende Aktionen:

```text
Command
```

Lesende Aktionen:

```text
Query
```

Beispiel:

```text
CreateTaskCommand
UpdateTaskCommand
DeleteTaskCommand
LockContextCommand
RunWorkflowCommand
```

gegen:

```text
GetPlanQuery
GetTaskQuery
GetContextQuery
GetWorkflowQuery
GetEvidenceQuery
GetDeviceQuery
```

---

# 47. EVENT SYSTEM

Jede wichtige Zustandsänderung erzeugt Events.

Beispiele:

```text
PLAN_CREATED
PLAN_UPDATED
TASK_CREATED
TASK_UPDATED
NODE_CREATED
NODE_UPDATED
NODE_DELETED
CONNECTION_CREATED
RESOURCE_ATTACHED
RESOURCE_CHANGED
EVIDENCE_CREATED
EVIDENCE_INVALIDATED
CONTEXT_LOCKED
CONTEXT_UNLOCKED
CONTEXT_CHANGED
CHALLENGE_COMPLETED
TRIAGE_COMPLETED
APPROVAL_GRANTED
APPROVAL_REJECTED
WORKFLOW_STARTED
WORKFLOW_PAUSED
WORKFLOW_COMPLETED
WORKFLOW_FAILED
WORKFLOW_BLOCKED
DEVICE_CONNECTED
DEVICE_DISCONNECTED
PERMISSION_GRANTED
PERMISSION_REVOKED
```

---

# 48. UI STATE MANAGEMENT

Mindestens getrennte Zustände:

```text
Plan State
Task State
Canvas State
Selection State
Context State
Resource State
Evidence State
Device State
Agent State
Execution State
Permission State
Validation State
Audit State
```

Lokale Canvas-Zustände wie:

```text
zoom
pan
selection
collapsed nodes
```

dürfen nicht mit fachlichem Plan-Zustand vermischt werden.

---

# 49. SERVER STATE VS CLIENT STATE

Client State:

```text
Canvas Position
Zoom
Open Panels
Selection
Temporary Filters
```

Server State:

```text
Plan
Task
Workflow
Resources
Evidence
Permissions
Context Lock
Execution
Versions
Audit
```

Der Client darf keinen serverseitig verbindlichen Zustand allein festlegen.

---

# 50. OPTIMISTIC UI

Optimistische UI-Aktualisierung darf nur bei reversiblen/niedrigen Risiken eingesetzt werden.

Beispiel:

```text
Node Position
```

Bei privilegierten Aktionen:

```text
Firmware Flash
EDL
Delete Database
Production Deploy
```

muss die UI auf die echte Backend-Bestätigung warten.

---

# 51. VALIDATION ENGINE

Validierung findet statt auf:

```text
Field
Component
Node
Connection
Task
Workflow
Plan
Context
Execution
```

Beispiele:

```text
Required field missing
Invalid reference
Permission missing
Dependency missing
Resource unavailable
Context conflict
Evidence invalid
Device unavailable
```

---

# 52. INLINE VALIDATION

Die UI muss Fehler direkt am Ursprung anzeigen.

```text
Node
 └── ⚠ Missing Permission
```

oder:

```text
Input
 └── 🔴 Invalid Device Reference
```

Zusätzlich globale Fehlerliste:

```text
3 errors
5 warnings
2 blocked
```

---

# 53. ERROR HANDLING

Jeder Fehler benötigt:

```text
Error ID
Type
Message
Context
Action
Retryable
Severity
Timestamp
Correlation ID
```

UI-Klassen:

```text
INFO
WARNING
ERROR
BLOCKED
CRITICAL
```

---

# 54. FEHLER-INTERAKTION

Beispiel:

```text
BLOCKED
Reason:
Device unavailable

[View Device]
[Check Connection]
[Retry]
[Change Resource]
```

Die UI darf Fehler nicht verschlucken.

---

# 55. SEARCH GLOBAL

Globale Suche über:

```text
Plans
Tasks
Workflows
Nodes
Files
Sources
Evidence
Devices
Agents
Runs
Logs
```

Suchergebnis zeigt:

```text
Type
Name
ID
Context
Status
Source
Related Task
```

---

# 56. FILTER

Filterbar nach:

```text
Status
Type
Project
Task
Device
Agent
Source
Evidence
Date
Version
Lock
Permission
Provider
```

Filter werden als UI-State gehalten und können gespeichert werden.

---

# 57. COMMAND PALETTE

Globale Command Palette:

```text
Create Task
Open Plan
Lock Context
Validate Plan
Run Workflow
Search Resource
Add Device
Add Agent
Run Challenge
Open Triage
Create Snapshot
Export Plan
```

Nur zulässige Commands werden als ausführbar angeboten.

---

# 58. KEYBOARD INTERACTIONS

Mindestens:

```text
Ctrl/Cmd + S
Ctrl/Cmd + Z
Ctrl/Cmd + Shift + Z
Ctrl/Cmd + C
Ctrl/Cmd + V
Ctrl/Cmd + F
Delete
Esc
Enter
Space
Arrow Keys
Shift
Ctrl/Cmd
```

Shortcuts dürfen keine Sicherheitsmechanismen umgehen.

---

# 59. CONTEXT MENUS

Je nach Objekt dynamisch:

```text
Plan:
Open
Lock
Validate
Run
Export
Archive

Task:
Open
Lock
Validate
Run
Duplicate

Node:
Edit
Duplicate
Connect
Inspect
Delete
Run

Resource:
Open
Preview
Link
Compare
Lock
```

---

# 60. DRAG-AND-DROP

Unterstützte Quellen:

```text
Resource → Node
Source → Evidence
Device → Task
Agent → Workflow
MCP Tool → Node
Task → Workflow Group
Node → Group
```

Jeder Drop erzeugt eine echte Modelländerung.

---

# 61. VERSION HISTORY UI

Zeigt:

```text
Version
Timestamp
Actor
Change
Affected Objects
Context Version
Git Commit
```

Actions:

```text
View
Compare
Restore
Branch
Create Snapshot
```

Restore erzeugt eine neue Version und überschreibt nicht zerstörend die Historie.

---

# 62. AUDIT UI

Audit Events:

```text
Who
What
When
Where
Why
Before
After
Permission
Context
Correlation ID
```

Audit darf nicht vom normalen Benutzerprozess editierbar sein.

---

# 63. LOGGING

Jede technische Ausführung erhält:

```text
Correlation ID
Run ID
Task ID
Workflow ID
Agent ID
Worker ID
Device ID
Timestamp
Severity
Event
Result
```

Logs müssen filterbar und exportierbar sein.

---

# 64. TELEMETRIE DER PLATTFORM

Nicht nur IoT-Telemetrie, sondern auch Plattformzustände:

```text
Worker CPU
Worker RAM
Queue
Latency
API Health
Database Health
Bridge Health
Device Health
Network Health
```

---

# 65. PROVIDER-ABHÄNGIGKEITEN

Externe Services werden über Adapter abstrahiert:

```text
Web Provider
LLM Provider
Embedding Provider
Reranker
Cloud
Storage
GitHub
Bright Data
Payment
External APIs
```

UI zeigt:

```text
Provider
Configured
Available
Quota
Latency
Policy
```

Kein Provider darf durch Mock-Ergebnisse ersetzt werden.

---

# 66. PROVIDER FALLBACK

Zulässiger Fallback:

```text
Provider A unavailable
        ↓
Triage
        ↓
Provider B
```

nur wenn:

```text
Policy erlaubt
Datenschutz erlaubt
Permission erlaubt
Output kompatibel
```

Nicht zulässig:

```text
Provider unavailable
→ fake success
```

---

# 67. CODE-/UI-DEPENDENCY-MAPPING

Jede UI-Funktion erhält eine technische Referenz:

```text
UI_FUNCTION_ID
        ↓
COMPONENT
        ↓
ROUTE
        ↓
STORE
        ↓
COMMAND / QUERY
        ↓
SERVICE
        ↓
DOMAIN
        ↓
ADAPTER
        ↓
RESOURCE
```

Beispiel:

```text
PLAN_LOCK_BUTTON
 ↓
ContextLockToolbar
 ↓
useContextActions()
 ↓
lockContext()
 ↓
LockContextCommand
 ↓
ContextLockService
 ↓
PolicyEngine
 ↓
ContextRepository
```

---

# 68. DEPENDENCY REGISTRY

Für jede Funktion wird registriert:

```text
Function
Frontend Component
Backend Endpoint / Command
Domain Service
Database
External Service
Permission
Feature Flag
Worker
Device Adapter
Tests
Documentation
```

Dadurch kann die Plattform feststellen:

```text
UI vorhanden
aber Backend fehlt
```

oder:

```text
Backend vorhanden
aber UI fehlt
```

oder:

```text
Dependency unavailable
```

---

# 69. FEATURE READINESS

Jede Funktion besitzt einen technischen Status:

```text
SPECIFIED
IMPLEMENTED
INTEGRATED
TESTED
VALIDATED
AVAILABLE
BLOCKED
NOT_CONFIGURED
NOT_VALIDATED
```

`IMPLEMENTED` darf nicht automatisch als `AVAILABLE` erscheinen.

---

# 70. UI FEATURE GATING

Die UI entscheidet auf Basis des tatsächlichen Zustands:

```text
AVAILABLE
→ Action enabled

BLOCKED
→ Action disabled + reason

NOT_CONFIGURED
→ Configure action

NOT_VALIDATED
→ Validation required

NO_PERMISSION
→ Permission request

DEPENDENCY_MISSING
→ Dependency view
```

---

# 71. KEINE FAKE INTERAKTION

Nicht zulässig:

```text
Button funktioniert optisch,
aber Backend existiert nicht.

Progress bar läuft,
aber keine Ausführung findet statt.

"Success" wird angezeigt,
ohne reales Ergebnis.

Device connected,
ohne reale Verbindung.

Payment complete,
ohne Provider-Bestätigung.

Build successful,
ohne echten Build.
```

---

# 72. LOADING STATES

Jede asynchrone Aktion benötigt einen echten Zustand:

```text
IDLE
LOADING
RUNNING
SUCCESS
FAILED
BLOCKED
CANCELLED
```

Bei langen Workflows zusätzlich:

```text
QUEUED
WAITING_PERMISSION
WAITING_APPROVAL
WAITING_DEVICE
WAITING_PROVIDER
```

---

# 73. OFFLINE / DISCONNECTED UI

Wenn Backend, Bridge oder Gerät nicht verfügbar ist:

```text
OFFLINE
```

Die UI zeigt den tatsächlichen Zustand.

Unterstützt werden kann:

```text
Read cached state
Queue allowed changes
Sync later
Conflict detection
```

Aber keine fiktive Bestätigung der noch nicht ausgeführten Aktion.

---

# 74. CONFLICT UI

Bei konkurrierenden Änderungen:

```text
YOUR VERSION
vs.
CURRENT VERSION
```

Optionen:

```text
Compare
Keep Mine
Keep Current
Merge
Cancel
```

Konfliktauflösung erzeugt eine neue Version.

---

# 75. ACCESS CONTROL UI

UI-Aktionen werden mindestens geprüft nach:

```text
User
Role
Project
Plan
Task
Resource
Permission
Context
Policy
Lease
```

---

# 76. SECRET HANDLING

Nicht in:

```text
UI
Logs
Workflow JSON
Exports
Agent Context
Audit Text
```

ablegen:

```text
Passwords
Private Keys
Tokens
Cookies
Session Secrets
API Secrets
```

Dafür:

```text
Secret Reference
Secret Store
Scoped Access
Audit
Expiration
```

---

# 77. API-UI-KONTRAKT

Jede UI-Aktion benötigt einen dokumentierten Vertrag:

```text
Request Schema
Response Schema
Errors
Auth
Permissions
Timeout
Retry
Idempotency
Audit Event
```

API-Schemas müssen automatisch gegen Frontend-Verträge getestet werden.

---

# 78. TESTARCHITEKTUR

Jede Funktion erhält:

```text
Unit Test
Component Test
Integration Test
Permission Test
Failure Test
E2E Test
Security Test
```

Für reale Hardware zusätzlich:

```text
Physical Device Test
```

---

# 79. INTERACTION TESTING

Beispiel:

```text
User clicks Lock
 ↓
Permission checked
 ↓
Context validated
 ↓
Backend command
 ↓
Lock persisted
 ↓
Audit event
 ↓
UI state updated
 ↓
Reload
 ↓
Lock still ACTIVE
```

Nicht nur:

```text
Button changes color
```

---

# 80. E2E-TESTS

Kompletter Ablauf:

```text
Create Plan
→ Create Task
→ Add Resource
→ Create Workflow
→ Add Node
→ Add Dependency
→ Lock Context
→ Challenge
→ Triage
→ Approval
→ Execute
→ Result
→ Replay
→ Version
→ Audit
```

---

# 81. SECURITY TESTS

Prüfen insbesondere:

```text
Unauthorized command
Permission escalation
Context bypass
Lock bypass
Secret leakage
Plaintext transmission
Invalid resource access
Cross-project access
Cross-task access
Expired lease
Revoked lease
```

---

# 82. DOCUMENTATION BINDING

Jede Funktion muss verknüpft sein mit:

```text
User Documentation
Developer Documentation
API Documentation
Test Documentation
Security Documentation
ADR
```

Nicht implementierte Funktionen werden nicht als vorhandene Features dokumentiert.

---

# 83. CODE-OWNERSHIP

Komponenten und Services erhalten klare Verantwortlichkeit:

```text
UI Team / Module
Application Service
Domain Owner
Infrastructure Adapter
Device Adapter
Security Owner
Test Owner
```

---

# 84. OBSERVABILITY

Jede relevante Aktion muss beobachtbar sein:

```text
Metrics
Logs
Traces
Audit
Events
```

Mit:

```text
Correlation ID
```

durch die komplette Kette.

---

# 85. PERFORMANCE

UI:

```text
Virtualization
Lazy Loading
Incremental Rendering
Memoization
Canvas Rendering
Web Workers
```

Backend:

```text
Async Execution
Queue
Worker Pool
Caching
Connection Pooling
```

Aber Caching darf die Evidence- oder Device-Wahrheit nicht verfälschen.

---

# 86. CACHE-REGELN

Trennung:

```text
UI Cache
Execution Cache
Resource Cache
RAG Cache
Memory
Archive
```

Kein Cache darf automatisch als aktuelle Live-Wahrheit dargestellt werden.

---

# 87. MOBILE / CT45P UI

Wegen begrenzter Hardware-Ressourcen:

```text
2-GB-HARDWARE-ZIEL
```

muss die UI auf dem Zielgerät ressourcenschonend arbeiten.

Schwere Berechnung wird bei Bedarf ausgelagert:

```text
CT45P
 ↓
Mobile / Edge Server
 ↓
Temporary Worker
 ↓
External Provider
```

unter Einhaltung von:

```text
Permission
Privacy
Policy
Resource
Latency
Cost
```

---

# 88. FREIE DARSTELLUNG

Der Nutzer kann für denselben PLAN unterschiedliche Präsentationen öffnen:

```text
Workflow
Table
Tree
Timeline
Graph
Network
3D
Signal
Document
Evidence
Dependency
```

Das fachliche Datenmodell bleibt identisch.

Nur die Presentation Layer ändert sich.

---

# 89. VIEW COMPOSER

Der Benutzer kann:

```text
View hinzufügen
View entfernen
View verschieben
View teilen
View synchronisieren
View speichern
View laden
```

Beispiel:

```text
LEFT:
Task Tree

CENTER:
Workflow Canvas

RIGHT:
Inspector

BOTTOM:
Execution Timeline
```

---

# 90. LINKED VIEWS

Auswahl in einer Ansicht synchronisiert die anderen.

Beispiel:

```text
Device im 3D-Modell gewählt
        ↓
Task markiert
        ↓
Workflow Node markiert
        ↓
Evidence gefiltert
        ↓
Inspector geöffnet
```

---

# 91. DATA PROVENANCE

Jeder angezeigte technische Wert muss seine Herkunft kennen:

```text
SOURCE
MEASUREMENT
CALCULATION
EXTERNAL_SOURCE
DEVICE
DATABASE
AGENT
USER
```

Bei Bedarf:

```text
Open Provenance
```

---

# 92. REALITY STATE

UI-Werte müssen unterscheiden zwischen:

```text
VERIFIED
MEASURED
CALCULATED
ESTIMATED
UNKNOWN
BLOCKED
```

Ein `UNKNOWN` darf nicht visuell wie ein bestätigter Wert erscheinen.

---

# 93. GLOBALER PLAN-AKTIONSRAUM

Über dem PLAN befindet sich ein globaler Aktionsbereich:

```text
[Save]
[Validate]
[Lock]
[Unlock]
[Challenge]
[Triage]
[Run]
[Pause]
[Stop]
[Emergency Stop]
[Compare]
[Version]
[Export]
```

Nicht erlaubte Aktionen sind:

```text
disabled
oder
nicht sichtbar
```

je nach Policy.

---

# 94. AKTIONSKETTE

Eine globale PLAN-Aktion muss denselben Kontrollpfad verwenden:

```text
USER INTERACTION
 ↓
UI ACTION
 ↓
AUTHORIZATION
 ↓
POLICY
 ↓
VALIDATION
 ↓
TRIAGE
 ↓
COMMAND
 ↓
DEPENDENCIES
 ↓
EXECUTION
 ↓
RESULT
 ↓
EVIDENCE
 ↓
AUDIT
 ↓
UI UPDATE
```

---

# 95. DESIGN TIME VS RUNTIME

Strict separation:

```text
DESIGN TIME
├── Edit
├── Configure
├── Connect
├── Plan
└── Validate

RUNTIME
├── Queue
├── Execute
├── Observe
├── Pause
├── Resume
└── Stop
```

Eine Designänderung darf eine laufende Ausführung nicht still manipulieren.

---

# 96. CONTEXT SNAPSHOT VOR AUSFÜHRUNG

Vor einem kritischen Run:

```text
PLAN CONTEXT
TASK CONTEXT
WORKFLOW VERSION
RESOURCE HASHES
EVIDENCE
DEVICE STATE
PERMISSIONS
POLICIES
```

werden zu einem Execution Context zusammengeführt.

```text
ExecutionContextID
```

Dieser bleibt für die Ausführung referenziert.

---

# 97. EXECUTION RESULT

Ergebnis:

```text
SUCCESS
PARTIAL
FAILED
BLOCKED
CANCELLED
UNKNOWN
```

Jeder Status benötigt eine nachvollziehbare Begründung.

---

# 98. ACCEPTANCE CRITERIA FÜR DIE GESAMTE UI

PLAN gilt funktional erst als fertig, wenn ein Benutzer real:

```text
PLAN öffnen
PLAN erstellen
PLAN bearbeiten
TASK erstellen
TASK bearbeiten
CONTEXT LOCK setzen
CONTEXT LOCK ändern
CONTEXT DIFF anzeigen
RESOURCE hinzufügen
SOURCE hinzufügen
EVIDENCE erzeugen
WORKFLOW erstellen
NODE erstellen
NODE bearbeiten
NODE verbinden
NODE löschen
WORKFLOW zoomen
WORKFLOW navigieren
AGENT hinzufügen
TOOL hinzufügen
DEVICE verbinden
PERMISSION konfigurieren
CHALLENGE ausführen
TRIAGE ausführen
APPROVAL durchführen
WORKFLOW validieren
WORKFLOW starten
WORKFLOW pausieren
WORKFLOW stoppen
ERGEBNIS sehen
REPLAY öffnen
VERSION vergleichen
VERSION wiederherstellen
AUDIT ansehen
EXPORT erstellen
```

kann.

---

# 99. TECHNISCHES ABNAHMEKRITERIUM

Für jede UI-Funktion muss nachweisbar sein:

```text
✓ UI vorhanden
✓ Interaction vorhanden
✓ Command/Query vorhanden
✓ Backend vorhanden
✓ Domain Logic vorhanden
✓ Dependencies vorhanden
✓ Permission vorhanden
✓ Validation vorhanden
✓ Error State vorhanden
✓ Audit vorhanden
✓ Test vorhanden
✓ Documentation vorhanden
```

Fehlt ein Teil:

```text
NOT COMPLETE
```

---

# 100. FEATURE TRACEABILITY MATRIX

Für das Projekt muss automatisch eine Matrix erzeugbar sein:

```text
Feature
→ UI
→ Action
→ Command
→ Service
→ Domain
→ Dependency
→ Permission
→ Test
→ Documentation
→ Status
```

Beispiel:

```text
Context Lock
│
├── UI: ContextLockToolbar
├── Action: LOCK_CONTEXT
├── Command: LockContextCommand
├── Service: ContextLockService
├── Domain: Context
├── Dependency: ContextRepository
├── Permission: PLAN_CONTEXT_LOCK
├── Test: ContextLockE2E
├── Security: LockBypassTest
└── Docs: context-lock.md
```

---

# 101. KEIN VERWAISTER CODE

Code ohne verwendete Funktion soll erkannt werden:

```text
Orphan Service
Orphan Endpoint
Orphan UI Component
Orphan Command
Orphan Database Table
Orphan Feature Flag
```

Ebenso:

```text
UI Feature
→ kein Backend
```

muss automatisch auffindbar sein.

---

# 102. KEINE Toten UI-BUTTONS

Jeder Button, jedes Menüelement, jede Tastenkombination und jede Drag-and-Drop-Aktion benötigt eine registrierte Action.

```text
UI Control
→ Action Registry
```

Nicht registrierte Interaktionen gelten als Fehler.

---

# 103. ACTION REGISTRY

Zentrale Struktur:

```text
ActionID
Name
UI Sources
Command
Permission
Policy
Input Schema
Output Schema
Status
Feature Flag
Audit Event
Tests
Documentation
```

Beispiele:

```text
PLAN_SAVE
PLAN_LOCK
PLAN_UNLOCK
TASK_CREATE
TASK_UPDATE
WORKFLOW_RUN
NODE_CREATE
NODE_DELETE
RESOURCE_ATTACH
EVIDENCE_CHALLENGE
TRIAGE_RUN
APPROVAL_GRANT
DEVICE_CONNECT
EMERGENCY_STOP
```

---

# 104. DEPENDENCY REGISTRY

Analog:

```text
DependencyID
Type
Provider
Version
RequiredBy
Availability
Health
Configuration
Permission
FallbackPolicy
```

Damit lässt sich im PLAN direkt beantworten:

> Warum ist diese Funktion gerade nicht ausführbar?

---

# 105. UI HEALTH CHECK

Das System soll selbst prüfen:

```text
UI Component
Action
API
Service
Dependency
Permission
```

und anzeigen:

```text
READY
DEGRADED
BLOCKED
NOT CONFIGURED
NOT VALIDATED
```

---

# 106. END-TO-END TRACE

Ein Benutzerklick muss bis zum technischen Ergebnis nachvollziehbar sein:

```text
CLICK
 ↓
Action ID
 ↓
Correlation ID
 ↓
Command
 ↓
Service
 ↓
Dependency
 ↓
Execution
 ↓
Result
 ↓
Evidence
 ↓
Audit
```

Diese Kette ist der zentrale Nachweis, dass eine Funktion tatsächlich real implementiert ist.

---

# 107. ABSCHLIESSENDES ARCHITEKTURPRINZIP

PLAN ist damit nicht nur:

```text
UI
```

und nicht nur:

```text
Workflow Editor
```

sondern:

```text
                    PLAN
                      │
       ┌──────────────┼──────────────┐
       │              │              │
      UI           CONTEXT        WORKFLOW
       │              │              │
INTERACTION        LOCK          EXECUTION
       │              │              │
     ACTION       EVIDENCE        AGENTS
       │              │              │
   COMMAND        CHALLENGE        TOOLS
       │              │              │
    SERVICE         TRIAGE        DEVICES
       │              │              │
    DOMAIN        DECISION        WORKERS
       │              │              │
 DEPENDENCIES   PERMISSIONS        RESULT
       │              │              │
       └──────────────┼──────────────┘
                      │
                 AUDIT / DATA
                      │
                 VERSIONING
```

## Zentrales Prinzip

> **Jede Benutzerinteraktion muss einen realen technischen Pfad besitzen.**
>
> **Jede UI-Aktion muss einem Command oder Query zugeordnet sein.**
>
> **Jeder Command muss validiert, autorisiert, ausgeführt, protokolliert und getestet werden.**
>
> **Jede Abhängigkeit muss bekannt und überprüfbar sein.**
>
> **Jeder reale Zustand muss vom System stammen und darf nicht durch Mock-/Demo-Daten ersetzt werden.**
>
> **Context Lock, Challenge, Triage, Permissions und Evidence sind Teil desselben technischen Kontrollpfades.**
>
> **Die UI darf nur den Zustand darstellen, den der darunterliegende Code tatsächlich liefern kann.**
>
> **UI, Code, Datenmodell, Services, Geräte, externe Provider und Tests müssen über eine vollständige Traceability-Kette miteinander verbunden sein.**

Damit ist die bestehende PLAN-Spezifikation jetzt auf die Ebene **„jede UI-Aktion → Code → Abhängigkeit → realer Zustand → Ergebnis → Audit/Test"** erweitert.
