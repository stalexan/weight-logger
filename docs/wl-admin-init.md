NAME
---
wl-admin-init — Initialize a deployment.

SYNOPSIS
---
```sh
wl-admin init {dev,prod} --homepage <HOMEPAGE> [--network <NETWORK>] [--http-host-port <HTTP_HOST_PORT>]
```

DESCRIPTION
---
Initializes a deployment, by creating the configuration files needed to build and run the Docker containers.

**_`wl-admin init prod --homepage <HOMEPAGE> [--network <NETWORK>] [--http-host-port <HTTP_HOST_PORT>]`_**

Initializes a __production deployment__, with the containers needed to run Weight
Logger in production mode.

**_`wl-admin init dev --homepage <HOMEPAGE> [--network <NETWORK>] [--http-host-port <HTTP_HOST_PORT>]`_**

Initializes a __development deployment__, with the containers needed to run Weight
Logger in development mode.

OPTIONS
---

**_`--homepage <HOMEPAGE>`_**

Specifies the homepage for the application. 

**_`--network <NETWORK>`_**

By default Weight Logger containers run in a network called `wl-network`.

This option overrides that, and runs the containers in the specified `NETWORK`.
This is useful for production deployments where a proxy to the application runs
in another Docker container. The network the proxy runs in is specified here,
and then traffic is then forwarded to the Weight Logger frontend.

The proxy should be configured to forward traffic to port 80 of `http://frontend/`.

**_`--http-host-port <HTTP_HOST_PORT>`_**

Specifies which host port the application should listen on, if any. By default,
the application is only visible within the Docker network, on port 80 of the
`proxy` container for a development deployment, and on port 80 of the
`frontend` container for a production deployment.

EXAMPLES
---

Initialize a __production deployment__ to be available from the URL
`http://www.foobar.com`, on port 80:

```sh
wl-admin init prod --homepage http://www.foobar.com --http-host-port 80
```

Initialize a __production deployment__ to be available from the URL
`https://www.foobar.com`, and run on port 80 of the `frontend` container within
the `my-network` Docker network:

```sh
wl-admin init prod --homepage https://www.foobar.com --network my-network
```

Initialize a __development deployment__ to be available from the URL
`http://localhost`, and run on run on port 80 of `localhost`:

```sh
wl-admin init dev --homepage http://localhost --http-host-port 80
```
