#!/usr/bin/env bash
# Real native debug APK build. No generated/mock data, no Gradle/Maven substitute.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/reports/android"; mkdir -p "$OUT"
printf '%s\n' 'BUILD_NOT_RUN; INSTALL_NOT_RUN' > "$OUT/build-status.txt"
WORK=""
cleanup() {
  rc=$?
  if [ "$rc" -ne 0 ]; then printf '%s\n' 'BUILD_BLOCKED_OR_FAILED; INSTALL_NOT_RUN' > "$OUT/build-status.txt"; fi
  if [ -n "$WORK" ]; then rm -rf "$WORK"; fi
  unset ATZE_ANDROID_TEMP_KEY_PASSWORD
}
trap cleanup EXIT
SDK="${ANDROID_SDK_ROOT:-${ANDROID_HOME:-}}"
[ -n "$SDK" ] || { echo 'BLOCKED: Android SDK not configured' >&2; exit 1; }
TOOLS="$SDK/build-tools/35.0.0"
PLATFORM="$SDK/platforms/android-35/android.jar"
for file in "$TOOLS/aapt2" "$TOOLS/d8" "$TOOLS/zipalign" "$TOOLS/apksigner" "$PLATFORM"; do
  [ -f "$file" ] || { echo 'BLOCKED: required Android SDK 35/build-tools 35.0.0 missing' >&2; exit 1; }
done
for tool in javac jar keytool zip; do command -v "$tool" >/dev/null || { echo "BLOCKED: $tool missing" >&2; exit 1; }; done
WORK="$(mktemp -d)"
PASS="$(python -c 'import secrets;print(secrets.token_urlsafe(32))')"
export ATZE_ANDROID_TEMP_KEY_PASSWORD="$PASS"
keytool -genkeypair -keystore "$WORK/debug.p12" -storetype PKCS12 -storepass:env ATZE_ANDROID_TEMP_KEY_PASSWORD -keypass:env ATZE_ANDROID_TEMP_KEY_PASSWORD -alias atze-debug -keyalg RSA -keysize 2048 -validity 30 -dname 'CN=Atze Ephemeral Development,OU=CI' >/dev/null 2>&1
build() {
  local module="$1" extra="$2"
  mkdir -p "$WORK/$module/classes" "$WORK/$module/dex"
  find "$ROOT/android/$module/src" -name '*.java' > "$WORK/$module/sources"
  javac -encoding UTF-8 -source 8 -target 8 -classpath "$PLATFORM${extra:+:$extra}" -d "$WORK/$module/classes" @"$WORK/$module/sources"
  jar cf "$WORK/$module/classes.jar" -C "$WORK/$module/classes" .
  "$TOOLS/d8" --lib "$PLATFORM" ${extra:+--classpath "$extra"} --min-api 26 --output "$WORK/$module/dex" "$WORK/$module/classes.jar"
  "$TOOLS/aapt2" link -I "$PLATFORM" --manifest "$ROOT/android/$module/AndroidManifest.xml" -o "$WORK/$module/unsigned.apk"
  (cd "$WORK/$module/dex" && zip -q -j "$WORK/$module/unsigned.apk" classes*.dex)
  "$TOOLS/zipalign" -f 4 "$WORK/$module/unsigned.apk" "$WORK/$module/aligned.apk"
  "$TOOLS/apksigner" sign --ks "$WORK/debug.p12" --ks-key-alias atze-debug --ks-pass env:ATZE_ANDROID_TEMP_KEY_PASSWORD --key-pass env:ATZE_ANDROID_TEMP_KEY_PASSWORD --out "$OUT/atze-$module-debug.apk" "$WORK/$module/aligned.apk"
  "$TOOLS/apksigner" verify --verbose --print-certs "$OUT/atze-$module-debug.apk" > "$OUT/$module-signature.txt"
}
build app ''
build test "$WORK/app/classes.jar"
(cd "$OUT" && sha256sum atze-*-debug.apk > SHA256SUMS)
printf '%s\n' 'BUILD_PASS; INSTALL_NOT_RUN' > "$OUT/build-status.txt"
printf '%s\n' 'BUILD PASS: actual debug APKs, ephemeral signing identity; installation NOT YET VALIDATED.'
