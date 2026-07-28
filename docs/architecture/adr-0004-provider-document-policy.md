# ADR-0004: Database-driven provider document policy

## Status

Accepted — 2026-07-28

## Decision

Store rider/merchant document requirements in normalized SQLite tables with
provider, service, country, effective dates, optional/required flags and JSON
metadata. Render upload controls from the requirement API. Store uploads outside
the web root and keep verification transitions in an append-only history.

## Why

Grab, Bolt, LINE MAN and Lalamove publish different Thailand flows and change
their checklists independently. Provider branches in frontend code would drift,
hide conditional documents and require a release for every policy change.

## Security consequences

The browser receives names, MIME limits and statuses, never provider secrets or
storage paths. Uploads are size/MIME/signature checked, randomised, private and
audited. Admin authentication is required for upload, review, status and
deletion. Runtime storage uses dedicated Fernet encryption at rest, provides a
hash-verified plaintext migration, and purges only aged soft-deletion
tombstones through an explicit scheduled command.

## Alternatives rejected

- Environment variables: not queryable, not versionable, and unsafe for PII.
- Hardcoded provider buttons: cannot represent effective dates or overrides.
- Public object storage: leaks identity documents and bypasses audit controls.
