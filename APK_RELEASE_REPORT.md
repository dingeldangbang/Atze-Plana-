# APK — PLAN candidate addendum

2026-09-14: PLAN changes are in Core/API/browser; native Android source unchanged, still read-only Core status (no PLAN editor/device bridge). New current-branch Android regression CI pending. The selected APK and its exact prior-source hashes below remain historical real evidence, not a newly built local APK or release. No JDK/SDK/ADB in this sandbox; no physical install/live-Core TLS/AAB acceptance added. Full-platform release BLOCKED.

---

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
