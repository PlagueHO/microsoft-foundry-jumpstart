#Requires -Modules @{ ModuleName="Az.Accounts"; ModuleVersion="5.3.2" }
#Requires -Modules @{ ModuleName="Az.Resources"; ModuleVersion="9.0.0" }
#Requires -Modules @{ ModuleName="Az.ManagedServiceIdentity"; ModuleVersion="2.0.0" }

<#
.SYNOPSIS
    Creates and configures Azure User Assigned Managed Identities for GitHub Actions and Copilot.

.DESCRIPTION
    This script creates two Azure User Assigned Managed Identities with Federated Credentials
    for GitHub repositories. It sets up the identities for GitHub Actions (test environment)
    and GitHub Copilot (copilot environment) with proper RBAC role assignments.

    The script creates:
    - A resource group in New Zealand North
    - Two User Assigned Managed Identities
    - Federated Credentials for GitHub OIDC authentication
    - RBAC role assignments (Contributor and conditional User Access Administrator)

.PARAMETER RepositoryName
    The name of the GitHub repository. This will be used to construct resource names
    and federated credential subject identifiers.

.PARAMETER Location
    The Azure location where resources will be created. Defaults to 'New Zealand North'.

.PARAMETER SubscriptionId
    The Azure Subscription ID where resources will be created. If not specified,
    the current subscription context will be used.

.PARAMETER GitHubOrganization
    The GitHub organization or user name that owns the repository. Defaults to 'PlagueHO'.

.PARAMETER Environment
    Array of GitHub environment names to create managed identities for. Defaults to @('test').
    Each environment will get its own managed identity and federated credential.
    The copilot environment is handled separately via the IncludeCopilot parameter.

.PARAMETER IncludeCopilot
    When true (default), creates a managed identity for GitHub Copilot coding agent.
    The identity is named 'mi-copilot-coding-agent' and uses the 'copilot' environment.

.PARAMETER Force
    Skips confirmation prompts and proceeds with resource creation/updates.

.EXAMPLE
    .\Update-AzureUserAssignedManagedIdentityForGitHub.ps1 -RepositoryName 'libris-maleficarum'

    Creates the managed identities for the libris-maleficarum repository using default location.

.EXAMPLE
    .\Update-AzureUserAssignedManagedIdentityForGitHub.ps1 -RepositoryName 'my-repo' -Force

    Creates the managed identities for my-repo repository without confirmation prompts.

.EXAMPLE
    .\Update-AzureUserAssignedManagedIdentityForGitHub.ps1 -RepositoryName 'my-repo' -SubscriptionId '12345678-1234-1234-1234-123456789012'

    Creates the managed identities in a specific Azure subscription.

.EXAMPLE
    .\Update-AzureUserAssignedManagedIdentityForGitHub.ps1 -RepositoryName 'my-repo' -Environment @('test', 'staging', 'prod')

    Creates managed identities for multiple environments plus the copilot environment.

.EXAMPLE
    .\Update-AzureUserAssignedManagedIdentityForGitHub.ps1 -RepositoryName 'my-repo' -IncludeCopilot:$false

    Creates managed identity for test environment only, without the copilot coding agent.

.OUTPUTS
    PSCustomObject
    Returns an object containing the created resource details including:
    - ResourceGroupName
    - Location
    - Identities (array of created managed identities)
    - RBACRoles
    - CreatedDate

.NOTES
    Author: GitHub Copilot
    Requires: Az.Accounts, Az.Resources, Az.ManagedServiceIdentity PowerShell modules
    Requires: User must be authenticated to Azure (Connect-AzAccount)
    Requires: User must have permissions to create resources and assign roles in the subscription

.LINK
    https://learn.microsoft.com/en-us/azure/active-directory/managed-identities-azure-resources/overview
#>

[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'High')]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$RepositoryName,

    [Parameter()]
    [ValidateNotNullOrEmpty()]
    [string]$Location = 'New Zealand North',

    [Parameter()]
    [ValidateNotNullOrEmpty()]
    [string]$SubscriptionId,

    [Parameter()]
    [ValidateNotNullOrEmpty()]
    [string]$GitHubOrganization = 'PlagueHO',

    [Parameter()]
    [ValidateNotNullOrEmpty()]
    [string[]]$Environment = @('test'),

    [Parameter()]
    [switch]$IncludeCopilot = $true,

    [Parameter()]
    [switch]$Force
)

#region Main Script

begin {
    Write-Verbose "Starting Azure User Assigned Managed Identity setup process"
    $ErrorActionPreference = 'Stop'

    #region Helper Functions

    function Initialize-AzureEnvironment {
    <#
    .SYNOPSIS
        Verifies Azure modules and authentication.
    
    .DESCRIPTION
        Checks that required Azure PowerShell modules are installed and loaded,
        then verifies Azure authentication and sets the subscription context.
    
    .PARAMETER SubscriptionId
        Optional subscription ID to set as the active context.
    
    .OUTPUTS
        Hashtable containing context information (Subscription, Tenant)
    #>
    [CmdletBinding()]
    param(
        [Parameter()]
        [string]$SubscriptionId
    )

    Write-Verbose "Checking for required Azure PowerShell modules"
    $requiredModules = @('Az.Accounts', 'Az.Resources', 'Az.ManagedServiceIdentity')
    
    foreach ($moduleName in $requiredModules) {
        if (-not (Get-Module -ListAvailable -Name $moduleName)) {
            throw "Required module '$moduleName' is not installed. Please install it using: Install-Module -Name $moduleName -Scope CurrentUser"
        }
        Import-Module -Name $moduleName -ErrorAction Stop
        Write-Verbose "Module '$moduleName' loaded successfully"
    }

    Write-Verbose "Verifying Azure authentication"
    $context = Get-AzContext
    if (-not $context) {
        throw "Not authenticated to Azure. Please run Connect-AzAccount first."
    }
    Write-Verbose "Authenticated as: $($context.Account.Id)"

    if ($SubscriptionId) {
        Write-Verbose "Setting subscription context to: $SubscriptionId"
        Set-AzContext -SubscriptionId $SubscriptionId | Out-Null
    }

    $currentSubscription = (Get-AzContext).Subscription
    Write-Verbose "Using subscription: $($currentSubscription.Name) ($($currentSubscription.Id))"

    return @{
        Subscription = $currentSubscription
        Tenant = $context.Tenant
    }
}

function New-GitHubResourceGroup {
    <#
    .SYNOPSIS
        Creates a resource group for GitHub integration resources.
    
    .DESCRIPTION
        Creates or verifies existence of an Azure Resource Group with appropriate tags
        for GitHub repository integration.
    
    .PARAMETER ResourceGroupName
        The name of the resource group to create.
    
    .PARAMETER Location
        The Azure location for the resource group.
    
    .PARAMETER RepositoryName
        The GitHub repository name for tagging.
    
    .PARAMETER Force
        Skip confirmation prompts.
    #>
    [CmdletBinding(SupportsShouldProcess = $true)]
    param(
        [Parameter(Mandatory = $true)]
        [string]$ResourceGroupName,

        [Parameter(Mandatory = $true)]
        [string]$Location,

        [Parameter(Mandatory = $true)]
        [string]$RepositoryName,

        [Parameter()]
        [switch]$Force
    )

    Write-Verbose "Checking for resource group: $ResourceGroupName"
    $resourceGroup = Get-AzResourceGroup -Name $ResourceGroupName -ErrorAction SilentlyContinue

    if (-not $resourceGroup) {
        if ($Force -or $PSCmdlet.ShouldProcess($ResourceGroupName, "Create Resource Group in $Location")) {
            Write-Verbose "Creating resource group: $ResourceGroupName in $Location"
            $resourceGroup = New-AzResourceGroup -Name $ResourceGroupName -Location $Location -Tag @{
                Purpose = 'GitHub Integration'
                ManagedBy = 'PowerShell Script'
                Repository = $RepositoryName
            }
            Write-Warning "Resource group '$ResourceGroupName' created in $Location"
        }
        else {
            throw "Resource group creation cancelled by user"
        }
    }
    else {
        Write-Verbose "Resource group '$ResourceGroupName' already exists"
    }

    return $resourceGroup
}

function New-GitHubManagedIdentity {
    <#
    .SYNOPSIS
        Creates a User Assigned Managed Identity.
    
    .DESCRIPTION
        Creates or verifies existence of an Azure User Assigned Managed Identity
        in the specified resource group.
    
    .PARAMETER ResourceGroupName
        The name of the resource group.
    
    .PARAMETER IdentityName
        The name of the managed identity to create.
    
    .PARAMETER Location
        The Azure location for the identity.
    
    .PARAMETER Force
        Skip confirmation prompts.
    
    .OUTPUTS
        Microsoft.Azure.Commands.ManagedServiceIdentity.Models.PsManagedIdentity
    #>
    [CmdletBinding(SupportsShouldProcess = $true)]
    param(
        [Parameter(Mandatory = $true)]
        [string]$ResourceGroupName,

        [Parameter(Mandatory = $true)]
        [string]$IdentityName,

        [Parameter(Mandatory = $true)]
        [string]$Location,

        [Parameter()]
        [switch]$Force
    )

    Write-Verbose "Processing managed identity: $IdentityName"
    $identity = Get-AzUserAssignedIdentity -ResourceGroupName $ResourceGroupName -Name $IdentityName -ErrorAction SilentlyContinue

    if (-not $identity) {
        if ($Force -or $PSCmdlet.ShouldProcess($IdentityName, "Create User Assigned Managed Identity")) {
            Write-Verbose "Creating managed identity: $IdentityName"
            $identity = New-AzUserAssignedIdentity -ResourceGroupName $ResourceGroupName -Name $IdentityName -Location $Location
            Write-Warning "Managed identity '$IdentityName' created"
            
            # Wait for the identity to propagate in Azure AD
            Write-Verbose "Waiting for identity to propagate in Azure AD..."
            Start-Sleep -Seconds 10
        }
        else {
            throw "Managed identity creation cancelled by user"
        }
    }
    else {
        Write-Verbose "Managed identity '$IdentityName' already exists"
    }

    return $identity
}

function New-GitHubFederatedCredential {
    <#
    .SYNOPSIS
        Creates a Federated Identity Credential for GitHub OIDC.
    
    .DESCRIPTION
        Creates or verifies existence of a Federated Identity Credential that allows
        GitHub Actions or Copilot to authenticate using OIDC.
    
    .PARAMETER ResourceGroupName
        The name of the resource group.
    
    .PARAMETER IdentityName
        The name of the managed identity.
    
    .PARAMETER CredentialName
        The name of the federated credential.
    
    .PARAMETER Subject
        The GitHub OIDC subject identifier.
    
    .PARAMETER Force
        Skip confirmation prompts.
    #>
    [CmdletBinding(SupportsShouldProcess = $true)]
    param(
        [Parameter(Mandatory = $true)]
        [string]$ResourceGroupName,

        [Parameter(Mandatory = $true)]
        [string]$IdentityName,

        [Parameter(Mandatory = $true)]
        [string]$CredentialName,

        [Parameter(Mandatory = $true)]
        [string]$Subject,

        [Parameter()]
        [switch]$Force
    )

    Write-Verbose "Processing federated credential: $CredentialName"
    $existingCredential = Get-AzFederatedIdentityCredential `
        -ResourceGroupName $ResourceGroupName `
        -IdentityName $IdentityName `
        -Name $CredentialName `
        -ErrorAction SilentlyContinue

    if (-not $existingCredential) {
        if ($Force -or $PSCmdlet.ShouldProcess($CredentialName, "Create Federated Credential")) {
            Write-Verbose "Creating federated credential: $CredentialName"
            Write-Verbose "Subject: $Subject"
            
            New-AzFederatedIdentityCredential `
                -ResourceGroupName $ResourceGroupName `
                -IdentityName $IdentityName `
                -Name $CredentialName `
                -Issuer 'https://token.actions.githubusercontent.com' `
                -Subject $Subject `
                -Audience @('api://AzureADTokenExchange') | Out-Null
            
            Write-Warning "Federated credential '$CredentialName' created"
        }
    }
    else {
        Write-Verbose "Federated credential '$CredentialName' already exists"
    }
}

function Grant-ManagedIdentityRBAC {
    <#
    .SYNOPSIS
        Assigns RBAC roles to a managed identity.
    
    .DESCRIPTION
        Assigns Contributor and conditional User Access Administrator roles to a
        managed identity at the subscription scope. The User Access Administrator
        role includes conditions to prevent assignment of privileged roles.
    
    .PARAMETER PrincipalId
        The principal ID of the managed identity.
    
    .PARAMETER IdentityName
        The name of the identity (for logging).
    
    .PARAMETER SubscriptionId
        The subscription ID for role scope.
    
    .PARAMETER Force
        Skip confirmation prompts.
    #>
    [CmdletBinding(SupportsShouldProcess = $true)]
    param(
        [Parameter(Mandatory = $true)]
        [string]$PrincipalId,

        [Parameter(Mandatory = $true)]
        [string]$IdentityName,

        [Parameter(Mandatory = $true)]
        [string]$SubscriptionId,

        [Parameter()]
        [switch]$Force
    )

    Write-Verbose "Configuring RBAC roles for $IdentityName"
    $subscriptionScope = "/subscriptions/$SubscriptionId"
    $maxRetries = 3
    $retryDelaySeconds = 5

    # Assign Contributor role
    $contributorRoleDefinitionId = (Get-AzRoleDefinition -Name 'Contributor').Id
    $contributorAssignment = Get-AzRoleAssignment `
        -ObjectId $PrincipalId `
        -RoleDefinitionId $contributorRoleDefinitionId `
        -Scope $subscriptionScope `
        -ErrorAction SilentlyContinue

    if (-not $contributorAssignment) {
        if ($Force -or $PSCmdlet.ShouldProcess("Contributor role to $IdentityName", "Assign role")) {
            Write-Verbose "Assigning Contributor role to $IdentityName"
            
            $retryCount = 0
            $success = $false
            while (-not $success -and $retryCount -lt $maxRetries) {
                try {
                    New-AzRoleAssignment `
                        -ObjectId $PrincipalId `
                        -RoleDefinitionName 'Contributor' `
                        -Scope $subscriptionScope `
                        -ErrorAction Stop | Out-Null
                    $success = $true
                    Write-Warning "Contributor role assigned to '$IdentityName'"
                }
                catch {
                    $retryCount++
                    if ($retryCount -lt $maxRetries) {
                        Write-Verbose "Role assignment failed (attempt $retryCount/$maxRetries). Waiting $retryDelaySeconds seconds before retry..."
                        Start-Sleep -Seconds $retryDelaySeconds
                    }
                    else {
                        Write-Warning "Failed to assign Contributor role after $maxRetries attempts: $_"
                        throw
                    }
                }
            }
        }
    }
    else {
        Write-Verbose "Contributor role already assigned to $IdentityName"
    }

    # Assign User Access Administrator role with conditions
    $userAccessAdminRoleDefinitionId = (Get-AzRoleDefinition -Name 'User Access Administrator').Id
    $uaaAssignment = Get-AzRoleAssignment `
        -ObjectId $PrincipalId `
        -RoleDefinitionId $userAccessAdminRoleDefinitionId `
        -Scope $subscriptionScope `
        -ErrorAction SilentlyContinue

    if (-not $uaaAssignment) {
        if ($Force -or $PSCmdlet.ShouldProcess("User Access Administrator role to $IdentityName", "Assign role with conditions")) {
            Write-Verbose "Assigning User Access Administrator role with conditions to $IdentityName"
            
            # Get role definition IDs for prohibited roles
            $ownerRoleId = (Get-AzRoleDefinition -Name 'Owner').Id
            $uaaRoleId = (Get-AzRoleDefinition -Name 'User Access Administrator').Id
            $rbacAdminRoleId = (Get-AzRoleDefinition -Name 'Role Based Access Control Administrator').Id

            # Create condition to deny assignment of privileged roles
            $condition = "((!(ActionMatches{'Microsoft.Authorization/roleAssignments/write'})) OR (@Request[Microsoft.Authorization/roleAssignments:RoleDefinitionId] ForAnyOfAnyValues:GuidNotEquals {$ownerRoleId, $uaaRoleId, $rbacAdminRoleId}))"
            $conditionVersion = '2.0'

            $retryCount = 0
            $success = $false
            while (-not $success -and $retryCount -lt $maxRetries) {
                try {
                    New-AzRoleAssignment `
                        -ObjectId $PrincipalId `
                        -RoleDefinitionName 'User Access Administrator' `
                        -Scope $subscriptionScope `
                        -Condition $condition `
                        -ConditionVersion $conditionVersion `
                        -ErrorAction Stop | Out-Null
                    $success = $true
                    Write-Warning "User Access Administrator role (with conditions) assigned to '$IdentityName'"
                    Write-Verbose "Condition prevents assignment of Owner, User Access Administrator, and RBAC Administrator roles"
                }
                catch {
                    $retryCount++
                    if ($retryCount -lt $maxRetries) {
                        Write-Verbose "Role assignment failed (attempt $retryCount/$maxRetries). Waiting $retryDelaySeconds seconds before retry..."
                        Start-Sleep -Seconds $retryDelaySeconds
                    }
                    else {
                        Write-Warning "Failed to assign User Access Administrator role after $maxRetries attempts: $_"
                        throw
                    }
                }
            }
        }
    }
    else {
        Write-Verbose "User Access Administrator role already assigned to $IdentityName"
    }
}

function Show-SetupSummary {
    <#
    .SYNOPSIS
        Displays setup summary and next steps.
    
    .DESCRIPTION
        Shows a formatted summary of created resources and instructions for
        configuring GitHub repository secrets and environments.
    
    .PARAMETER AzureContext
        Hashtable containing subscription and tenant information.
    
    .PARAMETER Identities
        Array of created managed identity objects.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [hashtable]$AzureContext,

        [Parameter(Mandatory = $true)]
        [array]$Identities
    )

    Write-Verbose "Displaying setup summary"
    Write-Host "`nNext Steps:" -ForegroundColor Cyan
    Write-Host "1. Add the following secrets to your GitHub repository:" -ForegroundColor Yellow
    Write-Host "   - AZURE_TENANT_ID: $($AzureContext.Tenant.Id)" -ForegroundColor White
    Write-Host "   - AZURE_SUBSCRIPTION_ID: $($AzureContext.Subscription.Id)" -ForegroundColor White
    
    $stepNumber = 2
    foreach ($identity in $Identities) {
        Write-Host "`n$stepNumber. For GitHub environment '$($identity.Environment)':" -ForegroundColor Yellow
        Write-Host "   - AZURE_CLIENT_ID: $($identity.ClientId)" -ForegroundColor White
        $stepNumber++
    }
    
    $environmentList = ($Identities.Environment | ForEach-Object { "'$_'" }) -join ', '
    Write-Host "`n$stepNumber. Create GitHub environments $environmentList in your repository settings" -ForegroundColor Yellow
}

    #endregion

    # Initialize Azure environment
    try {
        $azureContext = Initialize-AzureEnvironment -SubscriptionId $SubscriptionId
    }
    catch {
        throw "Azure environment initialization failed: $_"
    }
}

process {
    try {
        # Define resource names
        $resourceGroupName = "rg-github-$RepositoryName-mi"

        # Create resource group
        $resourceGroup = New-GitHubResourceGroup `
            -ResourceGroupName $resourceGroupName `
            -Location $Location `
            -RepositoryName $RepositoryName `
            -Force:$Force

        # Collection to store created identities
        $createdIdentities = @()

        # Add copilot environment if requested
        $environmentsToProcess = $Environment
        if ($IncludeCopilot) {
            $environmentsToProcess = $Environment + @('copilot')
        }

        # Process each environment
        foreach ($env in $environmentsToProcess) {
            Write-Verbose "Processing environment: $env"
            
            # Define identity name based on environment
            if ($env -eq 'copilot') {
                $identityName = 'mi-copilot-coding-agent'
            }
            else {
                $identityName = "mi-github-actions-$env-environment"
            }
            
            # Create managed identity
            $identity = New-GitHubManagedIdentity `
                -ResourceGroupName $resourceGroupName `
                -IdentityName $identityName `
                -Location $Location `
                -Force:$Force

            # Create federated credential
            $federatedCredentialName = "$GitHubOrganization-$RepositoryName-$env-env"
            $subject = "repo:$GitHubOrganization/$($RepositoryName):environment:$env"

            New-GitHubFederatedCredential `
                -ResourceGroupName $resourceGroupName `
                -IdentityName $identityName `
                -CredentialName $federatedCredentialName `
                -Subject $subject `
                -Force:$Force

            # Assign RBAC roles
            Grant-ManagedIdentityRBAC `
                -PrincipalId $identity.PrincipalId `
                -IdentityName $identityName `
                -SubscriptionId $azureContext.Subscription.Id `
                -Force:$Force

            # Add to collection
            $createdIdentities += [PSCustomObject]@{
                Environment = $env
                Name = $identityName
                ClientId = $identity.ClientId
                PrincipalId = $identity.PrincipalId
                FederatedCredentialName = $federatedCredentialName
                Subject = $subject
            }
        }

        # Output summary
        Write-Output ([PSCustomObject]@{
            ResourceGroupName = $resourceGroupName
            Location = $Location
            Identities = $createdIdentities
            RBACRoles = @('Contributor', 'User Access Administrator (conditional)')
            CreatedDate = Get-Date
        })
    }
    catch {
        Write-Error "Failed to create or configure managed identities: $_"
        throw
    }
}

end {
    Write-Verbose "Azure User Assigned Managed Identity setup process completed"
    
    Show-SetupSummary `
        -AzureContext $azureContext `
        -Identities $createdIdentities
}

#endregion
