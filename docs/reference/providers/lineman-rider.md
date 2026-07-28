# LINE MAN rider registration — Thailand

## Flow

Use the LINE MAN RIDER Thailand registration flow, verify the phone number,
complete the in-app profile and vehicle information, then wait for account
activation. The public page states registration is free and available across
Thailand.

## Information, documents and vehicle types

The public page describes the registration flow and vehicle-owner consent but
does not publish a stable, complete document checklist. The application
therefore returns an empty requirement list until an operator records a
provider-confirmed checklist. It must not use a synthetic "review-needed"
document row because that would render a misleading upload control. Vehicle
type and ownership consent are structured fields; supported types and city
availability must be confirmed in the current LINE MAN RIDER app.

## Verification and renewal

Treat submitted documents as pending until LINE MAN confirms activation.
Re-check licences, registration, tax and insurance when they expire or when
the provider requests an update. A failed or changed requirement must be
versioned with an effective date rather than silently replacing history.

## Thailand notes and reference

This adapter intentionally leaves the public checklist empty. It renders
provider-confirmed updates without requiring a frontend release.

- https://lineman.line.me/rider/
- https://lineman.line.me/riderbkk/
