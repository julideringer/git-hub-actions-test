#!/bin/bash

# Archivo JSON actual con permisos
current_permissions_file="src/permissions_lambda.json"

# Obtener el contenido del archivo JSON anterior directamente desde git
previous_permissions_json=$(git show HEAD~1:src/permissions_lambda.json)

# Realiza un diff para encontrar las diferencias
diff_output=$(diff <(echo "$previous_permissions_json") <(cat "$current_permissions_file"))

# Mostrar diferencias
echo "Diferencias encontradas:"
echo "$diff_output"

# Identificar las lambdas cambiadas
changed_lambdas=()

# Leer el contenido del archivo JSON actual
current_json=$(cat "$current_permissions_file")
previous_json=$(echo "$previous_permissions_json")

# Función para extraer acciones de una lambda
extract_actions() {
    local json=$1
    local lambda_name=$2
    echo "$json" | jq -r --arg name "$lambda_name" '.lambdas[$name].Statement[].Action[]'
}

# Iterar sobre las lambdas en el JSON actual
for lambda in $(echo "$current_json" | jq -r '.lambdas | keys[]'); do
    # Obtener las acciones de la lambda actual y anterior
    current_actions=$(extract_actions "$current_json" "$lambda")
    previous_actions=$(extract_actions "$previous_json" "$lambda")

    # Comparar las acciones
    if [ "$current_actions" != "$previous_actions" ]; then
        changed_lambdas+=("$lambda")
    fi
done

# Mostrar las lambdas que han cambiado
if [ ${#changed_lambdas[@]} -ne 0 ]; then
    echo "Las siguientes funciones Lambda han cambiado sus permisos:"
    for lambda in "${changed_lambdas[@]}"; do
        echo " - $lambda"
    done
else
    echo "No se encontraron cambios en los permisos de las funciones Lambda."
fi
