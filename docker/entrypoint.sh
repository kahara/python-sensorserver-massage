#!/bin/bash -l
set -e
if [ "$#" -eq 0 ]; then
  exec sensorserver_massage -vv docker_config.toml
else
  exec "$@"
fi
