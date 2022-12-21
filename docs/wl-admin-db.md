NAME
---
wl-admin-db — Backup and restore the database.

SYNOPSIS
---
```sh
wl-admin db backup <FILE>
wl-admin db restore <FILE>
```

DESCRIPTION
---
Backs up and restores the database.

**_`wl-admin db backup <FILE>`_**

Backs up the database to `<FILE>`.

**_`wl-admin db restore <FILE>`_**

Restores the database from `<FILE>`.

EXAMPLES
---

Backup the database to the file weight-logger-backup.sql:

```sh
wl-admin db backup weight-logger-backup.sql
```

Restore the database from file weight-logger-backup.sql:

```sh
wl-admin db restore weight-logger-backup.sql
```
