# Asset inventory and naming rules

## Naming

- Use lowercase kebab-case: `pork-neck-hero-01.webp`.
- Add the intended placement before an optional sequence: `launch-facebook-feed-01.png`.
- Keep editable sources (`.psd`, `.ai`, `.fig`) out of CDN deployment; put exported media beside them.
- Put original food photography in `food/menu-items/original/`, responsive derivatives in
  `thumbnail/` or `optimized/`, and never overwrite the original.
- Store generated images under `food/ai-generated/generated/` with a metadata sidecar that
  records prompt key, generator, model and review status.

## Delivery matrix

| Area | Destination | Expected output |
| --- | --- | --- |
| `branding/logo` | Web and app | SVG; raster app-icon exports added after approval |
| `social/*` | Organic social | Platform-native PNG, WebP or MP4 export |
| `ads/*` | Paid campaigns | Export plus campaign metadata; no raw audience data |
| `print/*` | Printer | Press-ready PDF with bleed and color profile |
| `food/*` | Menu and marketing | Original plus optimized WebP derivative |
| `icons`, `illustrations` | Product UI | Accessible SVG with `role`/label where applicable |
| `videos/*` | Marketing/tutorials | MP4/WebM export plus caption file when published |

The directory structure is intentionally tracked with `.gitkeep` where a real
approved asset is not yet available. These markers are not deployable media.
