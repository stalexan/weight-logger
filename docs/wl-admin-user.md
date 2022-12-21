NAME
---
wl-admin-user — Manage users.

SYNOPSIS
---
```sh
wl-admin user list
wl-admin user add <USERNAME> --goal <GOAL> [--english] 
wl-admin user delete <USERNAME>
wl-admin user chpassword <USERNAME>
```

DESCRIPTION
---
Manages users, by listing, adding, and deleting them, and changing passwords.

**_`wl-admin user list`_**

Lists current users.

**_`wl-admin user add <USERNAME> --goal <GOAL> [--english]`_**

Adds user `<USERNAME>` with weight goal `<GOAL>`. Units for weight log entries are
metric by default (kgs). The option `--english` sets them to English (lbs).

**_`wl-admin user delete <USERNAME>`_**

Deletes user.

**_`wl-admin user chpassword <USERNAME>`_**

Changes the user's password.
  
EXAMPLES
---

Create user Garfield with a goal weight of 150 lb:

```sh
wl-admin user add Garfield --goal 150 --english
```

Delete user Garfield:

```sh
wl-admin user delete Garfield
```
