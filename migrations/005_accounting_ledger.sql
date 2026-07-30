CREATE TABLE IF NOT EXISTS ledger_entries (
    id TEXT PRIMARY KEY,
    entry_date TEXT NOT NULL,
    reference TEXT NOT NULL,
    journal TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'posted' CHECK (state IN ('draft','posted','cancelled')),
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (source_type, source_id)
);

CREATE TABLE IF NOT EXISTS ledger_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id TEXT NOT NULL REFERENCES ledger_entries(id) ON DELETE CASCADE,
    account_code TEXT NOT NULL,
    account_name TEXT NOT NULL,
    debit INTEGER NOT NULL DEFAULT 0 CHECK (debit >= 0),
    credit INTEGER NOT NULL DEFAULT 0 CHECK (credit >= 0),
    CHECK ((debit = 0 AND credit > 0) OR (credit = 0 AND debit > 0))
);

CREATE INDEX IF NOT EXISTS ledger_entries_date_idx ON ledger_entries(entry_date, id);
CREATE INDEX IF NOT EXISTS ledger_lines_entry_idx ON ledger_lines(entry_id);
