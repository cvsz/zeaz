-- Non-destructive document-requirements migration.
-- The runtime also applies these CREATE TABLE IF NOT EXISTS statements for
-- SQLite installs that do not run a migration runner.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS providers (
  id TEXT PRIMARY KEY, slug TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
  country TEXT NOT NULL DEFAULT 'TH', status TEXT NOT NULL DEFAULT 'active',
  metadata TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS provider_services (
  id TEXT PRIMARY KEY, provider_id TEXT NOT NULL REFERENCES providers(id) ON DELETE CASCADE,
  slug TEXT NOT NULL, name TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'active',
  metadata TEXT NOT NULL DEFAULT '{}', UNIQUE(provider_id, slug)
);
CREATE TABLE IF NOT EXISTS merchant_types (
  id TEXT PRIMARY KEY, slug TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
  metadata TEXT NOT NULL DEFAULT '{}', status TEXT NOT NULL DEFAULT 'active'
);
CREATE TABLE IF NOT EXISTS vehicle_types (
  id TEXT PRIMARY KEY, slug TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
  metadata TEXT NOT NULL DEFAULT '{}', status TEXT NOT NULL DEFAULT 'active'
);
CREATE TABLE IF NOT EXISTS document_types (
  id TEXT PRIMARY KEY, slug TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
  subject_type TEXT NOT NULL, allowed_mime_types TEXT NOT NULL DEFAULT '[]',
  max_size_bytes INTEGER NOT NULL DEFAULT 10485760, metadata TEXT NOT NULL DEFAULT '{}',
  status TEXT NOT NULL DEFAULT 'active'
);
CREATE TABLE IF NOT EXISTS provider_document_requirements (
  id TEXT PRIMARY KEY, provider_id TEXT NOT NULL REFERENCES providers(id) ON DELETE CASCADE,
  service_id TEXT REFERENCES provider_services(id) ON DELETE SET NULL,
  subject_type TEXT NOT NULL, merchant_type_id TEXT REFERENCES merchant_types(id) ON DELETE SET NULL,
  vehicle_type_id TEXT REFERENCES vehicle_types(id) ON DELETE SET NULL,
  document_type_id TEXT NOT NULL REFERENCES document_types(id) ON DELETE RESTRICT,
  country TEXT NOT NULL DEFAULT 'TH', effective_from TEXT NOT NULL, effective_to TEXT NOT NULL DEFAULT '',
  metadata TEXT NOT NULL DEFAULT '{}', is_required INTEGER NOT NULL DEFAULT 0,
  is_optional INTEGER NOT NULL DEFAULT 0, display_order INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'active', created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS merchant_document_requirements (
  id TEXT PRIMARY KEY, merchant_type_id TEXT NOT NULL REFERENCES merchant_types(id) ON DELETE CASCADE,
  document_type_id TEXT NOT NULL REFERENCES document_types(id) ON DELETE RESTRICT,
  country TEXT NOT NULL DEFAULT 'TH', effective_from TEXT NOT NULL, effective_to TEXT NOT NULL DEFAULT '',
  metadata TEXT NOT NULL DEFAULT '{}', is_required INTEGER NOT NULL DEFAULT 0,
  is_optional INTEGER NOT NULL DEFAULT 0, display_order INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'active', created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS uploaded_documents (
  id TEXT PRIMARY KEY, provider_id TEXT REFERENCES providers(id) ON DELETE SET NULL,
  subject_type TEXT NOT NULL, subject_id TEXT NOT NULL,
  requirement_id TEXT REFERENCES provider_document_requirements(id) ON DELETE SET NULL,
  original_filename TEXT NOT NULL, storage_path TEXT NOT NULL UNIQUE, mime_type TEXT NOT NULL,
  size_bytes INTEGER NOT NULL, sha256 TEXT NOT NULL, expires_at TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'pending', metadata TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS document_verification (
  document_id TEXT PRIMARY KEY REFERENCES uploaded_documents(id) ON DELETE CASCADE,
  status TEXT NOT NULL, verified_by TEXT NOT NULL DEFAULT '', reason TEXT NOT NULL DEFAULT '',
  verified_at TEXT NOT NULL DEFAULT '', metadata TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS verification_history (
  id TEXT PRIMARY KEY, document_id TEXT NOT NULL REFERENCES uploaded_documents(id) ON DELETE CASCADE,
  status TEXT NOT NULL, actor_role TEXT NOT NULL, reason TEXT NOT NULL DEFAULT '',
  metadata TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_provider_requirements_lookup
  ON provider_document_requirements(provider_id, subject_type, country, status, display_order);
CREATE INDEX IF NOT EXISTS idx_merchant_requirements_lookup
  ON merchant_document_requirements(merchant_type_id, country, status, display_order);
CREATE INDEX IF NOT EXISTS idx_uploaded_documents_subject
  ON uploaded_documents(subject_type, subject_id, status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_verification_history_document
  ON verification_history(document_id, created_at DESC);
