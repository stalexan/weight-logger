#!/bin/bash

set -e

if [ "$1" = 'uvicorn' ]; then
    # Give wls read permission for /keys.
    chown -R wls:wls /keys

    # Rus backend as wls.
    exec gosu wls "$@"
fi

exec "$@"
