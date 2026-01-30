#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status.
# set -u # Treat unset variables as an error when substituting.
# set -o pipefail # The return value of a pipeline is the status of the last command to exit with a non-zero status.

echo "Starting sample data upload script..."

# Get environment variables from azd (use || true to prevent exit on missing values)
# Fall back to shell environment variables if azd env values are not set
deploy_sample_data=$(azd env get-value DEPLOY_SAMPLE_DATA 2>/dev/null || echo "")
if [ -z "$deploy_sample_data" ]; then
    deploy_sample_data="${DEPLOY_SAMPLE_DATA:-}"
fi

storage_account_name=$(azd env get-value AZURE_SAMPLE_DATA_STORAGE_ACCOUNT_NAME 2>/dev/null || echo "")
if [ -z "$storage_account_name" ]; then
    storage_account_name="${AZURE_SAMPLE_DATA_STORAGE_ACCOUNT_NAME:-}"
fi

resource_group_name=$(azd env get-value AZURE_RESOURCE_GROUP 2>/dev/null || echo "")
if [ -z "$resource_group_name" ]; then
    resource_group_name="${AZURE_RESOURCE_GROUP:-}"
fi

azure_network_isolation=$(azd env get-value AZURE_NETWORK_ISOLATION 2>/dev/null || echo "")
if [ -z "$azure_network_isolation" ]; then
    azure_network_isolation="${AZURE_NETWORK_ISOLATION:-}"
fi

if [ "$deploy_sample_data" != "true" ]; then
    echo "DEPLOY_SAMPLE_DATA is not 'true'. Skipping sample data upload."
    exit 0
fi

if [ -z "$storage_account_name" ]; then
    echo "Error: Sample data storage account name not found. Ensure 'azd env get-value AZURE_SAMPLE_DATA_STORAGE_ACCOUNT_NAME' works." >&2
    exit 1
fi

if [ -z "$resource_group_name" ]; then
    echo "Error: AZURE_RESOURCE_GROUP environment variable not found. Ensure 'azd env get-value AZURE_RESOURCE_GROUP' works." >&2
    exit 1
fi

script_dir="$(dirname "$0")"
sample_data_root_path="$script_dir/../sample-data"

if [ ! -d "$sample_data_root_path" ]; then
    echo "Warning: Sample data directory not found at $sample_data_root_path. Skipping upload." >&2
    exit 0
fi

public_ip=""
firewall_rule_added=false

cleanup() {
    if [ "$firewall_rule_added" = true ] && [ -n "$public_ip" ]; then
        echo "Removing temporary IP rule ($public_ip) from storage account $storage_account_name."
        if ! az storage account network-rule remove --account-name "$storage_account_name" --resource-group "$resource_group_name" --ip-address "$public_ip" --only-show-errors; then
            echo "Warning: Failed to remove network rule for IP $public_ip. Please remove it manually." >&2
        else
            echo "Successfully removed network rule for IP $public_ip."
        fi
    fi
}
trap cleanup EXIT # Register cleanup function to be called on script exit

if [ "$azure_network_isolation" = "true" ]; then
    echo "Network isolation is enabled. Adding temporary IP rule to storage account."
    public_ip=$(curl -s https://api.ipify.org | tr -d '\r\n')
    if [ -z "$public_ip" ]; then
        echo "Error: Failed to retrieve public IP address." >&2
        exit 1 # Critical error, cannot proceed safely with network isolation
    fi
    echo "Current public IP: $public_ip"
    if az storage account network-rule add --account-name "$storage_account_name" --resource-group "$resource_group_name" --ip-address "$public_ip" --only-show-errors; then
        firewall_rule_added=true
        echo "Successfully added network rule for IP $public_ip."
        echo "Waiting for 30 seconds for network rule to propagate..."
        sleep 30
    else
        echo "Error: Failed to add network rule for IP $public_ip to storage account $storage_account_name." >&2
        # Continue without rule if it failed, upload might fail but cleanup will still run.
    fi
fi

if ! find "$sample_data_root_path" -mindepth 1 -maxdepth 1 -type d | read; then
    echo "No subfolders found in $sample_data_root_path to upload."
    exit 0
fi

for folder_path in "$sample_data_root_path"/*/; do
    if [ -d "$folder_path" ]; then
        container_name=$(basename "$folder_path" | tr '[:upper:]' '[:lower:]') # Container names must be lowercase
        
        echo "Processing folder '$(basename "$folder_path")' to upload to container '$container_name'..."

        # Check if container exists, create if not
        if ! az storage container show --name "$container_name" --account-name "$storage_account_name" --auth-mode login --output none --only-show-errors 2>/dev/null; then
            echo "Container '$container_name' does not exist. Creating..."
            if ! az storage container create --name "$container_name" --account-name "$storage_account_name" --auth-mode login --public-access off --output none --only-show-errors > /dev/null; then
                echo "Error: Failed to create container '$container_name'." >&2
                continue # Skip to next folder
            fi
            echo "Container '$container_name' created successfully."
        else
            echo "Container '$container_name' already exists."
        fi

        echo "Uploading files from '$folder_path' to container '$container_name'..."
        if ! az storage blob upload-batch --account-name "$storage_account_name" --destination "$container_name" --source "$folder_path" --overwrite true --auth-mode login --only-show-errors > /dev/null; then
            echo "Error: Failed to upload files from '$folder_path' to container '$container_name'." >&2
        else
            echo "Successfully uploaded files from '$folder_path' to container '$container_name'."
        fi
    fi
done

echo "Sample data upload script finished."
