#!/usr/bin/env bash
# Copies the files of Swagger UI that /api/docs serves (no CDN) into src/prumo/static/swagger-ui/.
# To update: set VERSION and INTEGRITY from https://registry.npmjs.org/swagger-ui-dist
# (versions.<VERSION>.dist.integrity) and run `scripts/update-swagger-ui.sh` from backend/.
set -euo pipefail
cd "$(dirname "$0")/.."

VERSION="5.34.0"
INTEGRITY="sha512-H6tAIjr3XqE31PbkZl0OFya1ziRLDfTwh3J6OHdumPtPCLfjTnyLeagl/55kFNZcTOz9a9QI9WP0FXldwiGJag=="
FILES=(swagger-ui-bundle.js swagger-ui.css favicon-32x32.png LICENSE NOTICE)
TARGET="src/prumo/static/swagger-ui"

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
curl -fsSL "https://registry.npmjs.org/swagger-ui-dist/-/swagger-ui-dist-${VERSION}.tgz" \
  -o "$work/package.tgz"
actual="sha512-$(openssl dgst -sha512 -binary "$work/package.tgz" | base64 -w0)"
if [[ "$actual" != "$INTEGRITY" ]]; then
  echo "Checksum mismatch for swagger-ui-dist ${VERSION}" >&2
  exit 1
fi
tar -xzf "$work/package.tgz" -C "$work"
mkdir -p "$TARGET"
find "$TARGET" -mindepth 1 -delete
for file in "${FILES[@]}"; do
  [[ -f "$work/package/$file" ]] && cp "$work/package/$file" "$TARGET/$file"
done
echo "$VERSION" > "$TARGET/VERSION"
echo "Swagger UI ${VERSION} copied to ${TARGET}"
