# Disaster recovery

zERP has no independent persistent state. Recovery restores the MooPiew
service, its SQLite database, uploaded-document storage, configuration, and
the zERP build artifact. The repository's database backup/restore runbooks are
the authority. RPO/RTO and off-host encrypted retention must be approved before
production launch.
