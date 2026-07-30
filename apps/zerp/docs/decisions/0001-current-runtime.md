# ADR 0001: Current runtime boundary

**Status:** accepted for the current slice

The zERP browser workspace consumes MooPiew's protected operations API instead
of creating a second database or pretending that a static UI is an ERP.
Odoo/PostgreSQL adoption remains an explicit future decision because licensing,
tenancy, migration, and recovery requirements are not yet approved.
