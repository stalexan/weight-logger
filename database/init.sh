#!/bin/bash

# Load password.
source ../config/keys/keys-database.env && export PGPASSWORD="$POSTGRES_PASSWORD"

# Print message to stdout.
function message() {
    printf "$1\n"
}

# Print error message to stderr.
function errMessage() {
    printf "ERROR: $1\n"
} >&2

# Print error message to stderr and exit.
function errExit() {
    errMessage "$1"
    exit 1
}

