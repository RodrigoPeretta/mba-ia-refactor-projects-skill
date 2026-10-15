#!/usr/bin/env bash
# Uso: run-requests.sh <saida.md> [admin_token]
# Executa o roteiro de validação contra http://127.0.0.1:3000
OUT="$1"; TOKEN="$2"; BASE=http://127.0.0.1:3000
DIR="$(cd "$(dirname "$0")" && pwd)"; TMP="$DIR/tmp"; mkdir -p "$TMP"
: > "$OUT"
step() { # step <n> <method> <path> <bodyfile|-> <useToken 0|1>
  local n=$1 m=$2 p=$3 b=$4 t=$5
  local args=(-s -o "$TMP/$n.out" -D "$TMP/$n.hdr" -w "%{http_code}" -X "$m" -H "Content-Type: application/json")
  [ "$b" != "-" ] && args+=(--data-binary "@$DIR/requests/$b")
  [ "$t" = 1 ] && [ -n "$TOKEN" ] && args+=(-H "X-Admin-Token: $TOKEN")
  local code; code=$(curl "${args[@]}" "$BASE$p")
  local ct; ct=$(grep -i '^content-type' "$TMP/$n.hdr" | cut -d' ' -f2- | tr -d '\r' | cut -d';' -f1)
  printf '### %s %s %s\nrequest: %s token:%s\nstatus: %s\ncontent-type: %s\nbody: %s\n\n' "$n" "$m" "$p" "$b" "$t" "$code" "$ct" "$(cat "$TMP/$n.out")" >> "$OUT"
}
step 01 GET /api/admin/financial-report - 1
step 02 POST /api/checkout 02.json 0
step 03 POST /api/checkout 03.json 0
step 04 POST /api/checkout 04.json 0
step 05 POST /api/checkout 05.json 0
step 06 POST /api/checkout 06.json 0
step 07 GET /api/admin/financial-report - 1
step 08 DELETE /api/users/2 - 1
step 09 GET /api/admin/financial-report - 1
step 10 DELETE /api/users/abc - 1
step 11 POST /api/checkout 11.json 0
step 12 POST /api/checkout 12.json 0
