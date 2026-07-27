#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
for directory in \
  branding/logo branding/brand-kit branding/app-icons branding/watermark \
  social/{facebook,instagram,tiktok,youtube,line} \
  ads/google/{search,display,performance-max} ads/meta/carousel ads/tiktok ads/campaign/{launch,promotion,retargeting} \
  print/{menu,restaurant,packaging,signage} \
  food/categories/{pork,chicken,seafood,drinks,desserts} food/menu-items/{original,thumbnail,optimized} food/photography/{hero,lifestyle,restaurant} food/ai-generated/generated \
  icons/{ui,food,social,system} illustrations/{onboarding,empty-state,marketing,characters} \
  videos/{branding,marketing,tutorials} videos/social/{reels,shorts,tiktok}; do
  mkdir -p "$ROOT/$directory"
done
printf 'Asset directory structure is ready at %s\n' "$ROOT"
