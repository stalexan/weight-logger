NAME
---
wl-admin-docker — Manage docker containers.

SYNOPSIS
---
```sh
wl-admin docker build [--pull]
wl-admin docker list
wl-admin docker up
wl-admin docker down
wl-admin docker rm
```

DESCRIPTION
---
Manages docker containers, by building them, listing their status, bringing
them up and down, and removing them.

**_`wl-admin docker build [--pull]`_**

Builds the Docker containers. The `--pull` option will build from scratch, by
pulling any new base images, and not using any cached images.

**_`wl-admin docker list`_**

Lists all the Weight Logger Docker images, containers, volumes, and networks.

**_`wl-admin docker up`_**

Brings the Docker containers up.

**_`wl-admin docker down`_**

Brings the Docker containers down.

**_`wl-admin docker rm`_**

Removes all the Weight Logger Docker images, containers, volumes, and networks.
