# AXM-Analyse — Spezifikationsgrundlage des Struktur-Builder-Moduls (konservierte Zusammenfassung)

> **Framing-Notiz:** Dieses Dokument ist die **konservierte Zusammenfassung** der vom Nutzer eingefügten AXM-Analyse (September 2026), die die Spezifikationsgrundlage für das Struktur-Builder-Modul ([Vertrag](structure-builder.md)) bildet. Der Originaltext wurde im Gespräch eingefügt und nicht als Datei im Repository abgelegt; diese Zusammenfassung hält die entscheidenden Inhalte strukturtreu fest. **Alle Technologie-Nennungen sind Optionen und Vergleiche, keine Umsetzungs-Nachweise** — implementiert ist ausschließlich der MVP-Schritt v0.1 laut [Vertrag](structure-builder.md).

## Ausgangspunkt und Vorbild-Tools
Ziel war ein visuelles Architektur-/Agenten-Werkzeug („AXM") für den Bestand. Verglichene Vorbilder/Auslöser: **FlowMapp** (visuelle Sitemaps), **AutoGen Studio** (deklarative Agenten-Konfiguration), **Builder.io** (visuelles UI-Building), **A2UI** (adaptive, agentengesteuerte Oberflächen), **OpenUI** (generative UI) sowie **MCP Apps**. Fazit der Analyse: kein Fremdprodukt übernehmen, sondern die Idee (visuelle, versionierte Strukturmodelle + deterministische Generierung) in den bestehenden Evidence-Core-Vertrag integrieren — mit desselben Realitätsdisziplin (kein Mock, kein Fake-Fallback, CALCULATED statt Erfundensein).

## Bibliotheksmatrix (Optionen)
Die Analyse matrixierte Baukasten-Optionen (u. a. Graph-Speicherung: **JSON-Graph in vorhandener Datenbank vs. Neo4j** — Nutzer-Einordnung: beides „einfach"; Frontend: React-basierte Builder-Kanvases vs. vanilla JS/SVG; Generierung: Code-/UI-Generatoren vs. read-only Übersichten). Repo-Fit-Entscheidungen, die daraus für den MVP fielen und im [Vertrag](structure-builder.md) dokumentiert sind: **kein React/kein Build-Step** (vanilla JS + SVG, 2-GB-RAM-Zielhardware), **JSON-Graph in SQLite** über die bestehende Record-Tabelle, **Generierung als reine CALCULATED-Query** ohne jeden Dateischreib-Zugriff.

## Roadmap der Analyse (Personenmonate-Schätzungen, keine Terminzusagen)
- **MVP (v0.1, ~8 PM):** ① visueller Struktur-Builder (Sitemap + Komponentenbaum) mit Drag&Drop ② Knoten-Inspektor (Name, Typ, Berechtigungen) ③ automatische Generierung: Routing-Übersicht + leere UI-Placeholders ④ Live-Vorschau (statische Sitemap-Anzeige). **→ umgesetzt als dieses Inkrement** ([Vertrag](structure-builder.md)), inkl. ehrlicher Grenzen (Drag&Drop nur Ansichtsposition, Berechtigungen nur deklarativ).
- **v1.0 (~18 PM):** u. a. A2UI-/Agenten-Integration, kausale Validierung, Versionsvergleichs-UI, adaptive Präsentation. **PLANNED, nicht implementiert.**
- **v2.0 (~24 PM):** u. a. Unsicherheits-Visualisierung, Multi-Agenten. **PLANNED, nicht implementiert.**
- **Gantt ab 2027:** zeitliche Einordnung der Ausbaustufen; bewusst **ohne Liefertermin- oder Performancezusagen** (konsistent mit der Roadmap-Disziplin des Repos).

## Validierungsexperimente
Die Analyse benannte Validierungsexperimente (Nutzbarkeit des visuellen Builders, Determinismus der Generierung, Eignung der Modellgrenzen). Für v0.1 umgesetzt als: deterministische Generierung mit Manifest-Hash und byte-gleichem Wiederholungsnachweis (STR-004), Version-Pinning (STR-005) sowie echte Browser-Checks (BROWSER-AXM-01/02). Breitere Nutzer-Validierungsexperimente bleiben der v1.0-Stufe vorbehalten.

## Risiken (aus der Analyse, mit MVP-Handhabung)
- **Scope-Creep Richtung UI-Generator/Agenten-Plattform** → MVP strikt auf read-only CALCULATED-Ausgaben begrenzt; kein Code-Generator, kein Agentenloop.
- **Komplexitäts-/Abhängigkeitsrisiko (React, Graph-DB, Build-Steps)** → vanilla JS/SVG + SQLite-JSON-Graph; keine neue Laufzeit-Abhängigkeit.
- **Missverständnis „Berechtigungen = Autorisierung"** → vertraglich als deklarierte Metadaten ausgewiesen, explizit keine durchgesetzte Autorisierung.
- **Erfundene Inhalte in generierten Strukturen** → Platzhalter konstant `EMPTY`, Generierung ohne Schreibzugriff, Identitäts-/Hash-Prüfungen.
