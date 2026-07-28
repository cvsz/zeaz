---
name: document-upload-ux-enhancement-and-rotation-tooling
description: Workflow command scaffold for document-upload-ux-enhancement-and-rotation-tooling in zeaz.
allowed_tools: ["Bash", "Read", "Write", "Grep", "Glob"]
---

# /document-upload-ux-enhancement-and-rotation-tooling

Use this workflow when working on **document-upload-ux-enhancement-and-rotation-tooling** in `zeaz`.

## Goal

Enhances the user experience of document upload and adds or updates provider rotation tooling/scripts.

## Common Files

- `scripts/rotate-provider-secrets.sh`
- `scripts/provider-rotation.d/README.md`
- `web/components/document-upload/document-upload.css`
- `web/components/document-upload/document-upload.js`
- `web/document-admin.js`

## Suggested Sequence

1. Understand the current state and failure mode before editing.
2. Make the smallest coherent change that satisfies the workflow goal.
3. Run the most relevant verification for touched files.
4. Summarize what changed and what still needs review.

## Typical Commit Signals

- Update or add scripts for provider rotation (scripts/rotate-provider-secrets.sh, scripts/provider-rotation.d/README.md)
- Modify frontend styles and logic for document upload (web/components/document-upload/document-upload.css/js)
- Update admin interface (web/document-admin.js)

## Notes

- Treat this as a scaffold, not a hard-coded script.
- Update the command if the workflow evolves materially.