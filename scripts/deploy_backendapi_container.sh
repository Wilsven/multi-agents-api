#!/bin/bash

# Define infrastructure variables to exclude from --env-vars
infra_vars=(
    "APP_NAME"
    "RESOURCE_GROUP"
    "IMAGE_NAME"
    "IMAGE_TAG"
    "ENVIRONMENT_NAME"
    "REGISTRY_SERVER"
    "REGISTRY_USERNAME"
    "REGISTRY_PASSWORD"
    "LOGS_WORKSPACE_ID"
    "LOGS_WORKSPACE_KEY"
)

# Read .env file and set environment variables, collect app vars
env_file=".azure/agents/.env"
env_vars_list=()

if [ -f "$env_file" ]; then
    while IFS= read -r line; do
        # Skip empty lines and comments
        if [[ "$line" =~ ^[[:space:]]*$ ]] || [[ "$line" =~ ^[[:space:]]*# ]]; then
            continue
        fi
        
        # Match key=value pattern
        if [[ "$line" =~ ^[[:space:]]*([^#][^=]+)=(.*)$ ]]; then
            key=$(echo "${BASH_REMATCH[1]}" | xargs)
            value=$(echo "${BASH_REMATCH[2]}" | xargs)
            export "$key"="$value"
            
            # Check if key is not in infra_vars array
            if [[ ! " ${infra_vars[@]} " =~ " ${key} " ]]; then
                env_vars_list+=("$key=$value")
            fi
        fi
    done < "$env_file"
else
    echo "Error: .env file not found in current directory"
    exit 1
fi

# Join environment variables for --env-vars
env_vars_arg="${env_vars_list[*]}"

# Compose the full command
az_cmd="az containerapp up --name $APP_NAME --resource-group $RESOURCE_GROUP --image $REGISTRY_SERVER/multi-agents-api-api:$IMAGE_TAG --environment $ENVIRONMENT_NAME --logs-workspace-id $LOGS_WORKSPACE_ID --logs-workspace-key $LOGS_WORKSPACE_KEY --registry-server $REGISTRY_SERVER --registry-username $REGISTRY_USERNAME --registry-password $REGISTRY_PASSWORD --ingress external --target-port 8000 --env-vars $env_vars_arg"

az_update_cmd="az containerapp ingress cors enable --name $APP_NAME --resource-group $RESOURCE_GROUP --allowed-origins * --allowed-methods * --allowed-headers *"

# Print the command
echo "Running the following command:"
echo "$az_cmd"

# Execute the command
eval "$az_cmd"

# echo "Updating the ContainerApp:"
# eval "$az_update_cmd"
