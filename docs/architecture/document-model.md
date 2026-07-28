# Provider document model

The document model separates provider policy from the upload and verification
workflow. `providers` own provider identity; `provider_services` scope a
checklist to rider or merchant onboarding; `merchant_types` and
`vehicle_types` express conditions; `document_types` define safe upload
formats; requirement tables define effective, localised policy; uploaded files
and their verification history are immutable/auditable records.

## Relationships

```text
providers 1──* provider_services
providers 1──* provider_document_requirements *──1 document_types
merchant_types 1──* merchant_document_requirements *──1 document_types
vehicle_types 1──* provider_document_requirements
uploaded_documents *──1 provider_document_requirements
uploaded_documents 1──1 document_verification 1──* verification_history
```

## Normalized record

Every requirement has `country`, `effective_from`, `effective_to`,
`is_required`, `is_optional`, `display_order`, `status` and `metadata` JSON.
Metadata contains source references and provider-specific fields; it is not an
environment variable and never contains credentials. Uploaded files store a
random ID, original filename, MIME, size, SHA-256, encrypted/private storage
path and lifecycle status. Public APIs omit the storage path and file bytes.

## Examples

```json
{
  "provider": "bolt",
  "subject_type": "rider",
  "vehicle_type": "motorcycle",
  "document_slug": "driver-license",
  "is_required": true,
  "effective_from": "2024-01-01",
  "metadata": {"source": "https://bolt.eu/th-th/support/articles/4406002078610/"}
}
```

## Migration and administration

`migrations/001_provider_document_requirements.sql` uses only additive
`CREATE TABLE IF NOT EXISTS` and indexes. The runtime applies the same schema
for a fresh SQLite deployment. Admin screens should manage provider → service
→ requirement → ordering/required/optional → localization → version, while
existing uploaded records remain untouched when a requirement changes.

## Versioning and localization

Never edit an effective requirement in place. Close it with `effective_to`,
insert a new version, and keep the source URL and review timestamp in metadata.
Effective windows are end-exclusive UTC timestamps: a row is active when
`effective_from <= now < effective_to`, or when `effective_to` is empty.
Version creation uses an immediate write transaction so concurrent requests
cannot create sibling versions. Historical rows are read-only.
Names can later be localized by adding a translation table keyed by
`document_type_id` and locale; the current API returns canonical names and
metadata so a frontend can provide Thai/English labels without changing the
policy identity.

## Provider overrides

Use a provider requirement row for an override and a merchant requirement row
for the normalized baseline. Conditions are expressed by foreign keys and
metadata, not by provider-specific branches in Python or JavaScript. When a
provider does not publish a stable checklist, return a review-needed row and
do not invent required documents.
