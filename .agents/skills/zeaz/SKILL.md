---
name: zeaz
description: Repository-specific development patterns and workflows for MooPiew.
---

# zeaz Development Patterns

> Repository-maintained workflow guidance

## Overview
This skill captures repository-specific development patterns for the Python
service, React/TypeScript clients, deployment assets, and provider-document
workflow.

## Coding Conventions

- **File Naming:**
  Use the naming convention already established by the nearest package.
  _Example:_  
  ```
  document-upload.js
  provider-list-item.js
  ```

- **Import Style:**  
  Use relative imports.  
  _Example:_  
  ```js
  import { uploadDocument } from './document-upload.js';
  ```

- **Export Style:**  
  Use named exports.  
  _Example:_  
  ```js
  // In document-upload.js
  export function uploadDocument(file) { ... }
  ```

- **Commit Messages:**  
  Follow [Conventional Commits](https://www.conventionalcommits.org/), primarily using the `feat` prefix.  
  _Example:_  
  ```
  feat: add drag-and-drop support to document upload
  ```

## Workflows

### Document Upload Feature Development
**Trigger:** When adding or improving document upload functionality for providers  
**Command:** `/new-document-upload-feature`

1. **Update backend logic**  
   Modify backend files (e.g., `app.py`) to support new or changed document upload features.

2. **Database migrations**  
   Create or update SQL migration files (`migrations/*.sql`) to reflect new document requirements.

3. **Documentation**  
   Update or add documentation:
   - `docs/ARCHITECTURE.md`
   - `docs/DATABASE.md`
   - `docs/architecture/*.md`
   - `docs/reference/providers/*.md`
   - `docs/openapi.yaml`

4. **Changelog and Roadmap**  
   Update `CHANGELOG.md` and `ROADMAP.md` to reflect your changes.

5. **Frontend components**  
   Modify or add:
   - `apps/web/src/documents.tsx`
   - `apps/web/src/documents.css`
   - `apps/web/documents.html`
   - generated `web/platform/` output through `npm run publish:platform`

6. **Testing**  
   Update or add tests in `tests/test_documents.py`.

7. **Scripts and templates**  
   Update scripts or templates as needed, such as `templates/store-master-data.json` or `scripts/ci/test.sh`.

_Example: Adding a new document field to the upload component_
```tsx
// apps/web/src/documents.tsx
export function validateDocumentType(type: string): boolean {
  return type.length > 0;
}
```

### Document Upload UX Enhancement and Rotation Tooling
**Trigger:** When improving document upload UX or managing provider secret rotation  
**Command:** `/enhance-document-upload-ux`

1. **Provider rotation scripts**  
   Update or add:
   - `scripts/rotate-provider-secrets.sh`
   - `scripts/provider-rotation.d/README.md`

2. **Frontend UX improvements**  
   Modify:
   - `apps/web/src/documents.css`
   - `apps/web/src/documents.tsx`

3. **Admin interface**  
   Update `apps/web/src/documents.tsx` and republish the platform build.

_Example: Improving upload button styling_
```css
/* web/components/document-upload/document-upload.css */
.upload-btn {
  background: #007bff;
  color: #fff;
}
```

## Testing Patterns

- **Test File Naming:**
  Python regression tests use `tests/test_*.py`; TypeScript tests follow the
  nearest package convention.
  _Example:_  
  ```
  tests/test_documents.py
  ```

- **Framework:**
  Python tests use `unittest`; TypeScript validation uses repository npm
  scripts.
  _Example test structure:_  
  ```js
  python3 -m unittest tests.test_documents -v
  ```

## Commands

| Command                       | Purpose                                                         |
|-------------------------------|-----------------------------------------------------------------|
| /new-document-upload-feature   | Start a new provider document upload feature or enhancement     |
| /enhance-document-upload-ux    | Improve document upload UX or manage provider secret rotation   |
