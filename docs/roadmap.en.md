# Business-in-a-Box Generator Framework roadmap

## Purpose

Turn one business configuration file into a portable starter kit: a business
plan, operating recipes, marketing and brand guides, a financial workbook
seed, and printable brand assets.

## Delivery sequence

1. Foundation: repository structure, bilingual roadmap, project policies.
2. Core content: business plan, recipes, marketing and brand templates in
   English and Thai.
3. Generator: configuration schema, templates and shell scripts.
4. Automation: validation, packaging and release workflow.
5. Polish: example assets and release-ready archives.

## Definition of done

`./scripts/generate.sh examples/cafe.yaml output/cafe` creates a complete,
reviewable business kit without changing source templates. `./scripts/package.sh
output/cafe` produces a ZIP suitable for hand-off.

## Next enhancements

- Add locale-specific tax and labour assumptions.
- Generate XLSX workbooks from the financial CSV templates.
- Add PDF rendering and a web-based configuration editor.
