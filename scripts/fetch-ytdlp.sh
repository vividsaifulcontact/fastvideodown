#!/bin/bash
# Build-time: fetch the standalone yt-dlp binary (the repo does not store the
# 41MB binaries; Netlify downloads them fresh on every git-based deploy).
set -e
VER="2026.10.26"
URL="https://github.com/yt-dlp/yt-dlp/releases/download/${VER}/yt-dlp_linux"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMPBIN="$(mktemp)"
echo "Downloading yt-dlp ${VER} ..."
curl -L --fail -o "$TMPBIN" "$URL"
chmod +x "$TMPBIN"
for d in "$ROOT/netlify/functions/formats" "$ROOT/netlify/functions/download"; do
  mkdir -p "$d"
  cp "$TMPBIN" "$d/yt-dlp"
  chmod +x "$d/yt-dlp"
  echo "yt-dlp ready in $d"
done
rm -f "$TMPBIN"
