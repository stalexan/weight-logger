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

Initializes a production deployment, with the containers needed to run Weight
Logger in production mode. An Nginx container hosts a prebuilt version of the
React application, and proxies calls to a Python FastAPI container that runs
the backend.

**_`wl-admin init dev --homepage <HOMEPAGE> [--network <NETWORK>] [--http-host-port <HTTP_HOST_PORT>]`_**

Initializes a development deployment, with the containers needed to run Weight
Logger in development mode. An Nginx container proxies calls to a Node
container that runs the frontend React application, and to a Python FastAPI
container that runs the backend.

OPTIONS
---

**_`--homepage <HOMEPAGE>`_**

Specifies the homepage for the application. 

**_`--network <NETWORK>`_**

Specifies the Docker bridge network to join, if any. This is useful for
production deployments where a proxy to the application runs in another Docker
container.  The network for the proxy Docker container is specified here, and
then traffic is forwarded to the Weight Logger frontend.

If this option isn't specified, the application runs in a Docker network called
`wl-network`.

**_`--http-host-port <HTTP_HOST_PORT>`_**

Specifies which host port the application should be surfaced on, if any. By default,
the application is only surfaced from within the Docker network, on port 80 of the 
`proxy` container for a development deployment, and on port 80 of the `frontend` container
for a production deployment.

EXAMPLES
---

Initialize a production deployment to be available from the URL
`http://www.foobar.com`, and run on run on port 80 of `www.foobar.com`:

```sh
wl-admin init prod --homepage http://www.foobar.com --http-host-port 80
```

Initialize a production deployment to be available from the URL
`https://www.foobar.com`, and run on port 80 of the `frontend` container within
the `my-network` Docker network:

```sh
wl-admin init prod --homepage https://www.foobar.com --network my-network
```

Initialize a development deployment to be available from the URL
`http://localhost`, and run on run on port 80 of `localhost`:

```sh
wl-admin init dev --homepage http://localhost --http-host-port 80
```
