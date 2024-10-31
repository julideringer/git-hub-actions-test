#!/bin/bash

 # Encuentra las dependencias cambiadas
 changed_dependencies=$(git diff --name-only HEAD^ HEAD | grep -E '^src/(common_tools|trips_tools)/' | grep '\.py$')
echo "MOSTRAMOS changed_dependencies: $changed_dependencies"
