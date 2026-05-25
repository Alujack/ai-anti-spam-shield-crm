#!/usr/bin/env bash
# preflight-demo.sh — run ~5 min before the defense recording.
#
# Smoke-tests the 6 URLs used in the recording (3 safe, 3 phishing) against
# the live API and asserts the expected verdict. Side-effect: warms the
# Redis deep-scan cache so the live demo scans hit fast.
#
# Exits non-zero if any assertion fails — fix red items BEFORE pressing record.

set -u

API="${API:-https://aiscamshield.codes}"
TIMEOUT_S=90  # safe-lab scan can take ~9s cold; allow headroom

GREEN=$'\033[0;32m'
RED=$'\033[0;31m'
YELLOW=$'\033[1;33m'
RESET=$'\033[0m'

fail=0

print_header() {
  echo
  echo "==> $1"
}

# ---- Step 1: connectivity ----
print_header "Connectivity checks"

for url in "$API/health" "$API/safe-lab-demo/"; do
  code=$(curl -sk -o /dev/null -w '%{http_code}' --max-time 10 "$url" || echo 000)
  if [[ "$code" == "200" ]]; then
    echo "${GREEN}PASS${RESET}  $url -> $code"
  else
    echo "${RED}FAIL${RESET}  $url -> $code"
    fail=1
  fi
done

# ---- Step 2: URL scan assertions ----
print_header "URL scan assertions (warms cache as a side-effect)"

# Format: URL | expected isPhishing | allowed threatLevels (comma-sep)
declare -a CASES=(
  "https://www.google.com|false|NONE"
  "https://paypal.com|false|NONE"
  "https://github.com|false|NONE"
  "http://paypa1-secure-login.com/verify|true|HIGH,CRITICAL"
  "https://newsbwebmail.weebly.com/|true|MEDIUM,HIGH,CRITICAL"
  "https://aiscamshield.codes/safe-lab-demo/|true|CRITICAL"
)

for case in "${CASES[@]}"; do
  IFS='|' read -r url want_phish want_levels <<< "$case"

  start=$(date +%s)
  body=$(curl -sk --max-time "$TIMEOUT_S" \
    -X POST "$API/api/v1/phishing/scan-url" \
    -H 'Content-Type: application/json' \
    -d "{\"url\":\"$url\"}")
  elapsed=$(( $(date +%s) - start ))

  if [[ -z "$body" ]]; then
    echo "${RED}FAIL${RESET}  $url -> empty response after ${elapsed}s"
    fail=1
    continue
  fi

  # Extract isPhishing and threatLevel. data.* is the standard shape; some
  # responses also bubble fields to the top level.
  got=$(printf '%s' "$body" | python3 -c '
import sys, json
try:
    j = json.load(sys.stdin)
    d = j.get("data", j) or {}
    print(str(d.get("isPhishing", "")).lower(), (d.get("threatLevel") or d.get("threat_level") or "").upper(), sep="|")
except Exception as e:
    print(f"PARSE_ERROR|{e}")
' 2>/dev/null)

  got_phish="${got%%|*}"
  got_level="${got#*|}"

  level_ok=0
  IFS=',' read -ra allowed <<< "$want_levels"
  for a in "${allowed[@]}"; do
    if [[ "$got_level" == "$a" ]]; then level_ok=1; break; fi
  done

  if [[ "$got_phish" == "$want_phish" && "$level_ok" == "1" ]]; then
    echo "${GREEN}PASS${RESET}  $url -> phish=$got_phish level=$got_level (${elapsed}s)"
  else
    echo "${RED}FAIL${RESET}  $url -> phish=$got_phish level=$got_level (want phish=$want_phish, level in {$want_levels}) (${elapsed}s)"
    fail=1
  fi
done

# ---- Step 3: cache warm-up confirmation ----
print_header "Cache warm-up check (re-scan google.com — must be fast)"

start=$(date +%s%3N)
body=$(curl -sk --max-time 15 -X POST "$API/api/v1/phishing/scan-url" \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://www.google.com"}')
elapsed_ms=$(( $(date +%s%3N) - start ))

if [[ "$elapsed_ms" -lt 1500 ]]; then
  echo "${GREEN}PASS${RESET}  re-scan returned in ${elapsed_ms}ms (cache warm)"
else
  echo "${YELLOW}WARN${RESET}  re-scan took ${elapsed_ms}ms — cache may not be warm; live demo may be slow on first scan"
fi

# ---- Summary ----
echo
if [[ "$fail" == "0" ]]; then
  echo "${GREEN}ALL GREEN — safe to record.${RESET}"
  exit 0
else
  echo "${RED}One or more checks FAILED. Fix before recording.${RESET}"
  exit 1
fi
