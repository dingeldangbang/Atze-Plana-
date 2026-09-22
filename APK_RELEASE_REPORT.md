# Ausgewählte Entwicklungs-APK — Core Workspace 0.2-dev · 2026-09-15

**APK tatsächlich gebaut, entwicklungssigniert, im SDK-Emulator installiert/gestartet/getestet und als lokale Datei mit geprüftem Hash bereitgestellt. Vollplattformziel weiterhin NICHT erreicht.** Kein Produktionsrelease, keine physische Geräteabnahme und kein stabiler Signierschlüssel.

## Download und Provenance

- Lokale Benutzerdatei: `reports/android-download/atze-app-debug.apk` — **25.003 Bytes**. Nur diese App-APK installieren, nicht die Instrumentation-APK. Dateien unter `reports/` bleiben absichtlich außerhalb von Git.
- [Originales CI-Archiv](https://github.com/dingeldangbang/Atze-Plana-/actions/runs/34962325843/artifacts/10393128900), GitHub-Anmeldung ggf. erforderlich; Ablauf laut geprüften Metadaten **2026-09-29T11:19:13Z**. Kein dauerhaftes Release-Asset.
- [Tatsächlich erfolgreicher Android-CI-Lauf 34962325843](https://github.com/dingeldangbang/Atze-Plana-/actions/runs/34962325843), 3m40s.
- Branch-Source: `cf59dc7bc4d0ca47ee1c7c68dd7bab7995227531`.
- Tatsächlich gebauter PR-Merge: `efb3c73368312e3b463778edd725955a0c392dc7`; Elternbindung durch die GitHub-Commit-API unabhängig von den Artefaktmeldungen geprüft.
- Originalarchiv: `android-debug-efb3c73368312e3b463778edd725955a0c392dc7`, 35.418 Bytes, GitHub-Digest `sha256:243e83411c41203519cd5478af6ce870ddb77f750fca6b65cc9bcb119a238a06`. Dieser Archivhash ist **nicht** der APK-Hash.

**SHA-256 der gelieferten App-APK:**

```text
e94dcc41605c713ef7f17390a4eb8790c04d4ffc505c5fb3446be51573d09096
```

Signatur: RSA2048, APK Signature Scheme **v2 und v3 geprüft**, ein Signierer, `CN=Atze Ephemeral Development, OU=CI`. Zertifikat-SHA256:

```text
9fbc05fcb821bc476f30b968e7a86bd7017bb36cbe47d326fa81ae45812305c2
```

Der temporäre Entwicklungsschlüssel wurde im Build entfernt und nicht hochgeladen. Eine spätere APK ist nicht automatisch updatekompatibel; bestehende Installation/Daten nicht ungefragt löschen. Debuggable-Build nicht mit produktiven Credentials/Daten verwenden. Keine AAB-/Store-/Lizenz-/Produktionsfreigabe.

## Ausgeführte Prüfungen und Grenzen

| Nachweisachse / Gate | Tatsächliches Ergebnis |
|---|---|
| Implemented | Native Projekt-/Aufgabenanlage, paginierte Verzeichnisse, bestätigte Triage und PLAN-Status über bestehende Core-APIs |
| Configured | Kein Betriebs-Core/Token eingebettet; vom Nutzer gewählter HTTPS-Core erforderlich, derzeit **NOT CONFIGURED** für eine konkrete Betriebsinstanz |
| SDK35 Java→DEX→APK / zipalign | PASS im ausgewählten CI-Lauf |
| `apksigner verify` | PASS im CI, v2/v3; keine lokale apksigner-Ausführung behauptet |
| Emulatorinstallation, Activity-Start | PASS; Android35 SDK-Emulator, kein physisches Gerät |
| Instrumentation | `atze_result=PASS`, `INSTRUMENTATION_CODE: -1`; Empty State, Lifecycle-/Tokenleeren, ungültige Origins/Routes/Tokens, JSON-Verträge, TLS-Protokolle |
| API-Mirror → lokale APK | PASS: vollständige zehn Chunks, exakter Quellstand, Größe und SHA256 gegen separaten Buildnachweis geprüft |
| Lokale Datei | ZIP-CRC aller Einträge PASS, echte `AndroidManifest.xml`/`classes.dex`; DEX-Header geprüft |
| Quellgleichheit | Lokale Native-App-/Testquellen, Manifeste und Buildskript SHA256 stimmen mit ausgewähltem Build überein |
| Python-Regression | **187 PASS**, **97,81%** App-Coverage; 13 neue Android-Delivery-/Core-Vertragsfälle, keine Android-Code-Coverage daraus abgeleitet |
| Docs / Reality / Python build / dependency audit | PASS lokal; keine bekannten Dependency-Schwachstellen im ausgeführten Audit |
| Isolierter HTTP-Smoke + `python -O` | Je **43 Antworten PASS**, echte temporäre Core-/SQLite-/Challenge-Prozesse; synthetische Testeingaben, keine Betriebsdaten |
| Core-/Browser-CI | [34962325926](https://github.com/dingeldangbang/Atze-Plana-/actions/runs/34962325926) PASS; reale isolierte Browserpipeline, nicht native Android-Mutationsabnahme |
| Native HTTPS-End-to-End / erfolgreiche UI-Mutationen | **NOT VALIDATED**: Client und Core-Verträge separat getestet, kein realer Core-TLS-Roundtrip aus Android nachgewiesen |
| Physisches Android/Honeywell/USB/BLE/Repair, Agenten, Cloud, Unity, IoT | **NOT VALIDATED / NOT IMPLEMENTED**, siehe Modulmatrix |
| Vollplattform / Production Ready | **BLOCKED** |

## Nachweise erneut abrufen / installieren

```sh
python scripts/download_android.py --run-id 34962325843 --revision efb3c73368312e3b463778edd725955a0c392dc7
cd reports/android-download
sha256sum -c SHA256SUMS
```

Der erfolgreiche lokale Abruf enthält App-APK, `SHA256SUMS`, `artifact-evidence.json`, `app-signature.txt` und `source-sha256.txt`. Der optionale lokale Downloadpack `atze-plana-0.2-dev.zip` enthält dieselbe APK plus Nachweise und Installationshinweise; kein Schlüssel/Token. Test-APK verbleibt im Original-CI-Archiv (12.715 Bytes, SHA256 `53cb9d317836b183aedc2cb7754c3eff0d3e14cf65b1d68c4f0ecdf74586c736`).

Auf eigenem autorisiertem Android8+-Gerät die App-APK öffnen; Installationsberechtigung nur für die verwendete Quelle erlauben. Einen eigenen Core mit Android-vertrauenswürdigem HTTPS-Zertifikat nach [Quickstart](QUICKSTART.md) betreiben. App öffnen, Origin ohne Pfad und separaten Operator-/Reviewer-Token eingeben. Sichtbare Sitzung ausdrücklich autorisieren. Projekt anlegen/auswählen, Aufgabe registrieren; jede Mutation bestätigen. Ohne vorhandene Evidenz und Challenge bleibt Triage blockiert. Hintergrundwechsel/Trennen löscht lokale Sitzung, Anzeige und Entwürfe; gesendete Requests können nicht zurückgerufen werden. [Vollständiger begrenzter Appvertrag](android/README.md).

**Nächste Abnahme, nicht als umgesetzt ausgeben:** isolierter echter Android↔Core-TLS-Test mit vertrauenswürdigem Zertifikat, Rollen-/Fehler-/Mutations-/Lebenszyklusfällen; danach weitere native Core-Workflows. Fehlende Plattformmodule benötigen jeweils echte Adapter, Isolation/Policy und Geräte-/Providerzugang. Keine funktionslosen Modulschaltflächen hinzugefügt.

[Draft-PR #3](https://github.com/dingeldangbang/Atze-Plana-/pull/3); kein Merge, Release oder Deployment. Nachfolgende reine Berichtsänderungen ersetzen nicht dieses ausdrücklich ausgewählte APK-Artefakt.

---

# Verlauf des Workspace-Inkrements — 2026-09-15 · Core Workspace 0.2-dev

Ziel des Nutzers: vollständige Plattform, zunächst Entwicklungssignatur. **Dieses Inkrement erfüllt das Gesamtziel noch nicht.** Neu implementiert: native Projekt-/Aufgabenanlage und paginierte Verzeichnisse, bestätigte Triage-Anfrage, PLAN-Verzeichnis/Live-Status; ausschließlich bestehende Core-APIs. Kein gebündelter Core/Executor, keine Geräte-/Agenten-/Cloudintegration. [Exakter Clientvertrag](android/README.md).

Erster neuer [Android-CI-Lauf 34961828041](https://github.com/dingeldangbang/Atze-Plana-/actions/runs/34961828041): **Build, Signatur v2/v3, Emulatorinstallation/-start und Instrumentation PASS**. Branch-Source `b2c12ee`, gebauter PR-Merge `2e89ae703e4210ce0ee20a872bd0e9890fc2de80`. Core-/Browser-CI [34961828096](https://github.com/dingeldangbang/Atze-Plana-/actions/runs/34961828096) und Universe-CI [34961828167](https://github.com/dingeldangbang/Atze-Plana-/actions/runs/34961828167) ebenfalls PASS. Kein neuer lokaler Modelllauf.

**Dateiauslieferung dieses ersten Laufs fehlgeschlagen:** GitHub kürzt Check-Annotationen nach 4096 Zeichen. Der Downloader hat die unvollständigen 16000-Zeichen-Chunks abgelehnt; keine APK geschrieben. Korrektur: maximal 3600 Base64-Zeichen je Chunk, zehn Chunks / 27KB APK, eigener Trunkierungs-Negativtest. PR-Merge-Elternbindung des Downloaders ebenfalls ergänzt und getestet. Der nachfolgende zweite Lauf (aktueller Nachweis oben) hat die korrigierte Übertragung tatsächlich bestanden; der erste fehlgeschlagene Download bleibt als Fehler dokumentiert.

Lokaler SDK/JDK-Preflight blockiert; offizieller SDK-Download TLS-Verbindungsfehler, SDK-Emulator/KVM fehlt lokal. Direkter Actions-Blobdownload mit EOF gescheitert. Workflow-Dispatch hat mit Integrationsberechtigung HTTP403 abgelehnt; tatsächliche Ausführung wurde durch [Draft-PR #3](https://github.com/dingeldangbang/Atze-Plana-/pull/3) ausgelöst. Keine TLS-Prüfung abgeschaltet, keine GitHub-Veröffentlichung oder Produktionseinführung.

Native HTTPS-End-to-End-Verbindung, erfolgreiche Anlage aus dem Android-UI, physisches Gerät, Vollplattform und Produktionsfreigabe bleiben **NOT VALIDATED / BLOCKED**. Ein signierter Build allein ersetzt diese Gates nicht.

---

## Historische Nachweise vor dem Workspace-Inkrement (nicht aktueller Quellstand)

## MCP discovery scope addendum — 2026-09-14

Core-only metadata integration; no native Android source changes, no OS proxy/APN manipulation and no native MCP/tool client. Existing selected APK source/hashes below remain unchanged. New Android regression CI is separate from live Bright Data/device proof; no new physical install or provider validation claimed.

---

# APK-Nachweis — aktuell ausgewähltes Debug-Artefakt

## Abschließender CI-Nachweis69e6676

Der erweiterte Teststand und der Download-Fix sind auf **69e667659d9761e902b430db267163ee393357e0** tatsächlich erneut geprüft: [Core inklusive Browser34794084565](https://github.com/dingeldangbang/Atze-Plana-/actions/runs/34794084565), [zusätzlicher Core-Pushlauf34794082691](https://github.com/dingeldangbang/Atze-Plana-/actions/runs/34794082691), [echte Modell-/PLAN-Inferenz34794084699](https://github.com/dingeldangbang/Atze-Plana-/actions/runs/34794084699) und [Android Build/Emulator34794084629](https://github.com/dingeldangbang/Atze-Plana-/actions/runs/34794084629) **PASS**. Der zuvor gescheiterte Download wird damit nicht umetikettiert; neue echte Ausführung mit unveränderten TLS-/Hash-Gates erfolgreich. Dieser abschließende Nachweiskommentar ändert keine App-/Test-/Workflowfunktion. Nachfolgende reine Bericht-CI-Ergebnisse stehen im [PR](https://github.com/dingeldangbang/Atze-Plana-/pull/1).

Das ausgewählte Download-APK bleibt ausdrücklich das in APK_RELEASE_REPORT beschriebene1a919db-Artefakt; spätere ephemere Signaturen/Hashes werden nicht damit verwechselt. Vollplattform/Produktion weiterhin BLOCKED.

2026-09-14. **Tatsächlich gebaut, signaturgeprüft, im SDK-Emulator installiert, gestartet und getestet.** Kein Produktionsrelease; nativer read-only HTTPS-Core-Statusclient, kein PLAN-Editor/Device Bridge/Honeywell Repair.

## Download / Provenance
- [Aktuelles Originalarchiv mit App und Testnachweisen](https://github.com/dingeldangbang/Atze-Plana-/actions/runs/34793544458/artifacts/10329016310), GitHub-Anmeldung ggf. erforderlich.
- [Erfolgreicher Android-CI-Lauf34793544458](https://github.com/dingeldangbang/Atze-Plana-/actions/runs/34793544458).
- Branch-Source **1a919db830d18d38b59b3e08314d148107bb9d23**; gebauter PR-Merge **01fcd2d98f0120bcfb3f499a5d5bb0988451ebae**.
- Archiv `android-debug-01fcd2d98f0120bcfb3f499a5d5bb0988451ebae`,21241Bytes, GitHub-Digest `sha256:58fb6ae2ab0d92b7d0c625ba55ecda499485c6e424abe749fb05a39fb7827a22`.
- GitHub-Metadaten geprüft: nicht abgelaufen, vorgesehenes Ende **2026-09-28T00:45:20Z**;14Tage Retention, kein dauerhaftes Release-Asset.

| Datei | Bytes | SHA-256 |
|---|---:|---|
| **atze-app-debug.apk** — eigentliche App |16811|`fdd741d91a2eec50d6af07caaf13bee0df0eaa8c7819df5a8c19a8e071bf613a`|
| atze-test-debug.apk — nur Instrumentation |12715|`8f2aba3d0ec6d1386ef03518a32e94c0f77205c6c7048838f156d5dc16d08828`|

Originale Check-Annotation: `EMULATOR_INSTALL_START_TEST_PASS`, `atze_result=PASS`, `INSTRUMENTATION_CODE: -1`. Der frühere Build-Zwischenstatus INSTALL_NOT_RUN ist durch den späteren tatsächlichen Emulatortest ersetzt. Tests: installierter Appstart, Empty State, Klartext-/unsichere Origin-Ablehnung, Tokenleeren; keine Live-Core-Verbindung/physische Bridge getestet.

## Nutzung / offene Gates
Archiv aus GitHub laden, entpacken, **App-APK** anhand obigem Hash prüfen; Test-APK ist keine Benutzerapp. Auf eigenem autorisierten Gerät ist eine gesonderte Installation/Freigabe nötig. Hier keine lokale APK-Kopie behauptet: Blobdownload aus dieser Sandbox scheitert, GitHub-Metadaten/Annotationen sind tatsächlich gelesen. Kein JDK/SDK/ADB hier; reale Androidausführung fand in CI statt.

Ephemerer Debugschlüssel wurde nicht hochgeladen und zerstört; spätere Builds haben andere Signatur/Hashes. Kein garantierter Same-Key-Updatepfad; ggf. separat autorisierte Neuinstallation mit Datenverlust-Risiko, keine automatische Geräteaktion. AAB, stabile Produktionssignatur, physisches Honeywell, reale Core-TLS-Session, Security-/Store-/Lizenzabnahme weiterhin BLOCKED/NOT RUN. Folgende Dokumentations-/Testcommits ändern keine Native-Android-Quellen; das **hier ausgewählte Artefakt bleibt ausdrücklich dieser Lauf**, nicht der jeweils neueste ephemeral signierte Build.

---

## Historisches, inzwischen ersetztes ausgewähltes Artefakt

# APK Release Report — actual development APK, full release BLOCKED

Stand 2026-09-14. **Debug-APK tatsächlich gebaut, signaturgeprüft, im SDK-Emulator installiert, gestartet und getestet.** Begrenzter nativer Read-only-Core-Statusclient, kein Android Repair-/Device-/Agent Builder.

## Geprüftes Artefakt
- Source branch commit: `b7912227f2a021cc3664b27e5984312369b1328e`.
- PR merge build revision: `c9d5f9c31349013fbc7bc0bdeabb3adedce4ca01` (GitHub Actions baut PR-Merge, nicht nur Branch-HEAD).
- [Erfolgreicher Android-Lauf 34790349728](https://github.com/dingeldangbang/Atze-Plana-/actions/runs/34790349728), 3m19s.
- [Original APK-/Nachweisarchiv](https://github.com/dingeldangbang/Atze-Plana-/actions/runs/34790349728/artifacts/10328670450) (GitHub-Anmeldung ggf. erforderlich; Retention14Tage, kein Release-Asset).
- Archivname `android-debug-c9d5f9c31349013fbc7bc0bdeabb3adedce4ca01`, 29390Bytes; GitHub-Artefaktdigest `sha256:85687dfd30bc5baaf6b71671be8727d02656ffa36e0448ef2413669c78a02c68`.

| Datei | Bytes | SHA-256 |
|---|---:|---|
| **atze-app-debug.apk** — eigentliche App | 16811 | `b7893a6d8e4da3650b21c75d10796d7db4032410c2a5be65ee7c45af30f03b14` |
| atze-test-debug.apk — nur Instrumentation, nicht Kunden-App | 12715 | `7f5c478eb4e9b401b7e9eb4af5481b0c66f4396daf1c05718aa2c088a2744ee0` |

Diese Hashes wurden in der CI aus tatsächlichen APK-Bytes berechnet und als Check-Annotation über authentifizierte GitHub API gelesen, nicht erfunden. Lokaler ZIP-Transfer aus dem GitHub-Blob-Store scheitert in Arena mit EOF; daher keine lokale APK-Kopie behauptet. Originale sind über den obigen GitHub-Artefaktlink lieferbar. Android-Quellcode bleibt bei nachfolgenden reinen Dokumentations-/Report-Hygieneänderungen unverändert. Neue Debugbuilds haben wegen neuer ephemerer Schlüssel andere Hashes; nicht diese Hashes auf fremde Builds anwenden.

## Tatsächliche Gates
| Gate | Ergebnis |
|---|---|
| SDK35 / Java→DEX / APK-Paket | PASS im genannten CI-Lauf |
| Debugsignatur + apksigner verify | PASS; temporärer RSA-Schlüssel, kein Produktionskey |
| adb install app und test APK | PASS auf tatsächlich gestartetem SDK-Emulator |
| Activity start | PASS |
| Instrumentation | `atze_result=PASS`, `INSTRUMENTATION_CODE: -1` |
| Finale Emulatorphase | `EMULATOR_INSTALL_START_TEST_PASS` |
| Native UI-/Security-Scope | Empty State, HTTP/unsafe origins blockiert, Tokenfeld geleert, TLS-Protokolle auf1.2/1.3 begrenzt |
| Reale Core-Verbindung aus APK | NOT RUN — kein Emulator-Live-Backend-/TLS-Handshaketest behauptet |
| Physisches Android/Honeywell/Repair/USB/BLE | NOT RUN / NOT IMPLEMENTED |
| AAB | NOT BUILT |
| Production signing, Play Store, Gesamtplattformrelease | BLOCKED |

SDK-Emulator ist eine tatsächliche virtuelle Android-Runtime, kein physisches Gerät. `build-status.txt` protokolliert den früheren reinen Buildschritt (INSTALL_NOT_RUN); der spätere `validation-status.txt` protokolliert die tatsächlich bestandene Installation/Startprüfung. Nicht vermischen.

## Nutzung / Einschränkungen
Aus ZIP die **atze-app-debug.apk** entnehmen und den passenden SHA256 prüfen. Keine Test-APK für normale Benutzung erforderlich. Debugbuild ohne dauerhaft verwalteten Updatekey; Neuinstallation eines anders signierten Builds kann explizite Deinstallation erfordern. Keine automatische Löschung von Nutzer-Appdaten oder Umgehung der Android-Signaturprüfung. [Clientvertrag und Buildanleitung](android/README.md). Kein operativer Server/Token eingebettet, nur explizit gewählter HTTPS-Core; alle Datenanforderungen bleiben authentifiziert, kein Zugriff auf echte Device-/Repair-Schnittstellen.

## Beobachtete Fehler, nicht verschwiegen
Lokal fehlen JDK/SDK; realer Buildpreflight BLOCKED. Erster CI-Lauf34789954436 baute/signierte APKs, Emulatorphase Timeout124. Diagnose34790257621 zeigte `Unknown AVD name`, fehlende ini im gesuchten AVD-Home. Korrigiert mit gemeinsamen expliziten ANDROID_AVD_HOME/ANDROID_USER_HOME/ANDROID_EMULATOR_HOME und ini-Prüfung. Erst der danach wirklich erfolgreiche Lauf34790349728 ist Installations-/Startnachweis.

Kein GitHub-Release erstellt, keine produktive Auslieferung behauptet. Artefaktlink ist ein realer zeitlich begrenzter CI-Download, keine dauerhafte Releaseveröffentlichung.
