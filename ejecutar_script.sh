#!/bin/bash

changed_dependencies=$(git diff --name-only HEAD^ HEAD | grep -E '^src/(common_tools|trips_tools)/' | grep '\.py$')
echo "hola"
echo $changed_dependencies
# Verifica la longitud de la variable
if [ ${#changed_dependencies} -gt 0 ]; then
    echo "Se encontraron cambios en las dependencias: $changed_dependencies"
else
    echo "No se encontraron cambios en las dependencias."
fi
