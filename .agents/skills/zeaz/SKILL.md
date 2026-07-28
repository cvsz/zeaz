```markdown
# zeaz Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill teaches you the core development patterns and workflows used in the `zeaz` JavaScript codebase. You'll learn the project's coding conventions, how to contribute new features or enhancements—especially around document upload functionality—and how to follow the repository's established workflows for consistent, maintainable code.

## Coding Conventions

- **File Naming:**  
  Use kebab-case for filenames.  
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
   - `web/components/document-upload/*`
   - `web/document-admin.html`
   - `web/document-admin.js`
   - `web/documents.html`

6. **Testing**  
   Update or add tests in `tests/test_documents.py`.

7. **Scripts and templates**  
   Update scripts or templates as needed, such as `templates/store-master-data.json` or `scripts/ci/test.sh`.

_Example: Adding a new document field to the upload component_
```js
// web/components/document-upload/document-upload.js
export function validateDocumentType(type) {
  // new validation logic
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
   - `web/components/document-upload/document-upload.css`
   - `web/components/document-upload/document-upload.js`

3. **Admin interface**  
   Update `web/document-admin.js` as needed.

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
  Test files use the `*.test.*` pattern.  
  _Example:_  
  ```
  document-upload.test.js
  ```

- **Framework:**  
  No specific testing framework detected.  
  _Example test structure:_  
  ```js
  // document-upload.test.js
  import { uploadDocument } from './document-upload.js';

  test('uploads a valid document', () => {
    // test logic here
  });
  ```

## Commands

| Command                       | Purpose                                                         |
|-------------------------------|-----------------------------------------------------------------|
| /new-document-upload-feature   | Start a new provider document upload feature or enhancement     |
| /enhance-document-upload-ux    | Improve document upload UX or manage provider secret rotation   |
```