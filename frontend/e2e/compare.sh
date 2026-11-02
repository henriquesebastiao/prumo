#!/usr/bin/env bash
# Side-by-side images: design/v1 board (left) | implementation screenshot (right).
set -euo pipefail
cd "$(dirname "$0")"
DESIGN=../../design/v1
OUT=output
mkdir -p "$OUT/compare"
pair() {
  local design="$DESIGN/$1" shot="$OUT/$2" name="$3"
  [[ "$1" == ../* ]] && design="$OUT/${1#../output/}"
  [[ -f "$design" && -f "$shot" ]] || { echo "skip $name"; return; }
  magick "$design" "$shot" -resize x2400 +append -resize 2880x "$OUT/compare/$name.png"
  echo "compare/$name.png"
}
pair "Login.png" login-light.png login
pair "Início — claro.png" composition-home-light.png home-light
pair "Início — escuro.png" composition-home-dark.png home-dark
pair "Início — claro.png" home-light.png shell-light
pair "Configurações.png" settings-light.png settings
pair "Estados vazio, carregando, erro, exclusão.png" composition-states-light.png states
magick "$DESIGN/Início — celular.png" -crop 780x1688+0+0 +repage "$OUT/design-mobile-top.png"
pair "../output/design-mobile-top.png" home-mobile.png home-mobile
