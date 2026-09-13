# APK Release Report — development candidate, not a release

Stand 2026-09-14. Actual local tool inspection: no java/javac/gradle/adb/sdkmanager/emulator/aapt/apksigner in PATH, no ANDROID_HOME/ANDROID_SDK_ROOT. Local `scripts/build_android.sh` actually attempted: BLOCKED, Android SDK not configured (`reports/android-local-preflight.log`). No local APK fabricated.

## Current candidate
Native read-only Core status client, source in [android](android/README.md). Build pipeline uses official SDK35 + Java tools, temporary debug key, real APK signing/verification/hashes. Separate CI emulator installation/launch/instrumentation required. **Workflow code is not evidence of a successful APK build.**

| Gate | Current evidence |
|---|---|
| Native client implemented | YES, bounded read-only scope |
| Local build | BLOCKED — missing JDK/SDK |
| CI build/sign/hash | NOT RUN at report creation |
| APK file available | NOT VERIFIED until artifact confirmed |
| Emulator install/start/tests | NOT RUN at report creation |
| Physical Android/Honeywell/Repair | NOT RUN / NOT IMPLEMENTED |
| Actual Core TLS integration from APK | NOT RUN |
| AAB | NOT BUILT |
| Production signing/release | BLOCKED; no production key used |

Final CI results and exact checksum/artifact references must be added after actual execution. No production distribution, Play Store release or repair capability claimed. Debug key must never be committed/uploaded; only certificate fingerprint and signed APK are deliverables.

## Beobachtete CI-Zwischenergebnisse
Erster Lauf34789954436: SDK-Build/Signaturprüfung tatsächlich PASS, Emulatorphase Timeout124, kein Installations-PASS. Diagnose-Lauf34790257621: tatsächliche APKs erstellt; Emulator37.1.11 meldet `Unknown AVD name [atze-test]`, fehlende ini im gesuchten AVD-Home. Nicht als erfolgreich installiert ausgegeben. Korrektur: gemeinsame explizite ANDROID_AVD_HOME/ANDROID_USER_HOME/ANDROID_EMULATOR_HOME für avdmanager und emulator, feste AVD-Path- und ini-Prüfung. Erneute Installation/Startprüfung notwendig.
