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
