#!/bin/sh -e
set -x

ruff sapphire_backend config docs scripts --fix
ruff format sapphire_backend config docs scripts
