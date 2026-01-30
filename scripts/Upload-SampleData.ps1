$ErrorActionPreference = "Stop"

Write-Host "Starting sample data upload script..."

# azd hooks automatically preload environment variables from the .env file into shell environment.
# However, variables set via 'azd env set' before provisioning may not be preloaded yet.
# Use azd env get-value to reliably retrieve all values from the azd environment.

$deploySampleData = azd env get-value DEPLOY_SAMPLE_DATA 2>$null
$storageAccountName = azd env get-value AZURE_SAMPLE_DATA_STORAGE_ACCOUNT_NAME 2>$null
$resourceGroupName = azd env get-value AZURE_RESOURCE_GROUP 2>$null
$azureNetworkIsolation = azd env get-value AZURE_NETWORK_ISOLATION 2>$null

Write-Host "DEBUG: DEPLOY_SAMPLE_DATA='$deploySampleData'"
Write-Host "DEBUG: AZURE_NETWORK_ISOLATION='$azureNetworkIsolation'"
Write-Host "DEBUG: AZURE_SAMPLE_DATA_STORAGE_ACCOUNT_NAME='$storageAccountName'"
Write-Host "DEBUG: AZURE_RESOURCE_GROUP='$resourceGroupName'"

if ($deploySampleData -ne "true") {
    Write-Host "DEPLOY_SAMPLE_DATA is not 'true'. Skipping sample data upload."
    exit 0
}

if (-not $storageAccountName) {
    Write-Error "Sample data storage account name not found. Ensure 'azd env get-value AZURE_SAMPLE_DATA_STORAGE_ACCOUNT_NAME' works."
    exit 1
}

if (-not $resourceGroupName) {
    Write-Error "AZURE_RESOURCE_GROUP environment variable not found. Ensure 'azd env get-value AZURE_RESOURCE_GROUP' works."
    exit 1
}

$sampleDataRootPath = Join-Path $PSScriptRoot "..\" "sample-data"
if (-not (Test-Path $sampleDataRootPath)) {
    Write-Warning "Sample data directory not found at $sampleDataRootPath. Skipping upload."
    exit 0
}

$publicIp = $null
$firewallRuleAdded = $false

try {
    if ($azureNetworkIsolation -eq "true") {
        Write-Host "Network isolation is enabled. Adding temporary IP rule to storage account."
        try {
            $publicIp = (Invoke-RestMethod -Uri 'https://api.ipify.org').Trim()
            If (-not $publicIp) {
                Write-Error "Failed to retrieve public IP address."
                exit 1
            }
            Write-Host "Current public IP: $publicIp"
            az storage account network-rule add --account-name $storageAccountName --resource-group $resourceGroupName --ip-address $publicIp --only-show-errors | Out-Null
            if ($LASTEXITCODE -ne 0) {
                Write-Error "Failed to add network rule for IP $publicIp to storage account $storageAccountName."
                # Continue without rule if it failed, upload might fail but cleanup will still run.
            } else {
                $firewallRuleAdded = $true
                Write-Host "Successfully added network rule for IP $publicIp."
                Write-Host "Waiting for 30 seconds for network rule to propagate..."
                Start-Sleep -Seconds 30
            }
        } catch {
            Write-Error "Error getting public IP or adding firewall rule: $($_.Exception.Message)"
            # Decide if to exit or continue; for now, continue, upload might fail.
        }
    }

    $foldersToUpload = Get-ChildItem -Path $sampleDataRootPath -Directory
    if ($foldersToUpload.Count -eq 0) {
        Write-Host "No subfolders found in $sampleDataRootPath to upload."
        exit 0
    }

    foreach ($folder in $foldersToUpload) {
        $containerName = $folder.Name.ToLowerInvariant() # Container names must be lowercase
        $sourceFolderPath = $folder.FullName

        Write-Host "Processing folder '$($folder.Name)' to upload to container '$containerName'..."

        # Check if container exists, create if not
        az storage container show --name $containerName --account-name $storageAccountName --auth-mode login --output none --only-show-errors | Out-Null
        if ($LASTEXITCODE -ne 0) { # Container does not exist
            Write-Host "Container '$containerName' does not exist. Creating..."
            az storage container create --name $containerName --account-name $storageAccountName --auth-mode login --public-access off --output none --only-show-errors | Out-Null
            if ($LASTEXITCODE -ne 0) {
                Write-Error "Failed to create container '$containerName'."
                continue # Skip to next folder
            }
            Write-Host "Container '$containerName' created successfully."
        } else {
            Write-Host "Container '$containerName' already exists."
        }

        Write-Host "Uploading files from '$sourceFolderPath' to container '$containerName'..."
        az storage blob upload-batch --account-name $storageAccountName --destination "$containerName" --source "$sourceFolderPath" --overwrite true --auth-mode login --only-show-errors | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to upload files from '$sourceFolderPath' to container '$containerName'."
        } else {
            Write-Host "Successfully uploaded files from '$sourceFolderPath' to container '$containerName'."
        }
    }
}
finally {
    if ($firewallRuleAdded -and $publicIp) {
        Write-Host "Removing temporary IP rule ($publicIp) from storage account $storageAccountName."
        az storage account network-rule remove --account-name $storageAccountName --resource-group $resourceGroupName --ip-address $publicIp --only-show-errors | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Failed to remove network rule for IP $publicIp. Please remove it manually."
        } else {
            Write-Host "Successfully removed network rule for IP $publicIp."
        }
    }
}

Write-Host "Sample data upload script finished."
