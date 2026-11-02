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
pair "Início — claro.png" garage-home-light.png garage-home-light
pair "Início — escuro.png" garage-home-dark.png garage-home-dark
pair "Veículos · Lista — claro.png" garage-list-light.png garage-list-light
pair "Veículos · Lista — escuro.png" garage-list-dark.png garage-list-dark
pair "Veículos · Detalhe do veículo.png" garage-detail.png garage-detail
pair "Veículos · Detalhe da manutenção.png" garage-maintenance.png garage-maintenance
pair "Veículos · Registrar manutenção.png" garage-dialog-maintenance.png garage-dialog-maintenance
pair "Veículos · Registrar abastecimento.png" garage-dialog-fueling.png garage-dialog-fueling
pair "Veículos · Registrar troca de óleo.png" garage-dialog-oil.png garage-dialog-oil
pair "Veículos · Atualizar km.png" garage-dialog-km.png garage-dialog-km
pair "Veículos · Cadastro edição.png" garage-dialog-vehicle.png garage-dialog-vehicle
magick "$DESIGN/Início — celular.png" +repage "$OUT/design-mobile-full.png"
pair "../output/design-mobile-full.png" garage-home-phone.png garage-home-phone
