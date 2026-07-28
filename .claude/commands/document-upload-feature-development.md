---
name: document-upload-feature-development
description: Workflow command scaffold for document-upload-feature-development in zeaz.
allowed_tools: ["Bash", "Read", "Write", "Grep", "Glob"]
---

# /document-upload-feature-development

Use this workflow when working on **document-upload-feature-development** in `zeaz`.

## Goal

Implements or enhances provider document upload features, including backend, frontend, documentation, and tests.

## Common Files

- `app.py`
- `migrations/*.sql`
- `docs/ARCHITECTURE.md`
- `docs/DATABASE.md`
- `docs/architecture/*.md`
- `docs/reference/providers/*.md`

## Suggested Sequence

1. Understand the current state and failure mode before editing.
2. Make the smallest coherent change that satisfies the workflow goal.
3. Run the most relevant verification for touched files.
4. Summarize what changed and what still needs review.

## Typical Commit Signals

- Update backend logic (e.g., app.py)
- Create or modify database migrations for document requirements
- Update or add documentation (docs/ARCHITECTURE.md, docs/DATABASE.md, docs/architecture/*, docs/reference/providers/*, docs/openapi.yaml)
- Update changelog and roadmap
- Modify or add frontend components (web/components/document-upload/*, web/document-admin.html/js, web/documents.html)

## Notes

- Treat this as a scaffold, not a hard-coded script.
- Update the command if the workflow evolves materially.