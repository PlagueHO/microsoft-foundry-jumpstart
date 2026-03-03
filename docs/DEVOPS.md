# DevOps Approach: CI/CD Strategy and Workflows

This document outlines the DevOps strategy, automated testing, and CI/CD workflows used in the Microsoft Foundry Secure Hub Solution Accelerator.

## Overview

The project leverages GitHub Actions for continuous integration (CI) and continuous delivery (CD) to ensure secure, reliable, and automated deployment of Azure infrastructure and application resources. All workflows are defined as YAML files in the `.github/workflows` directory.

## CI/CD Workflow Summary

| Workflow File | Purpose |
|---------------|---------|
| `continuous-integration.yml` | Runs on pull requests to the `main` branch. Triggers linting and publishing of Bicep templates to validate code quality early. |
| `continuous-delivery.yml` | Runs on pushes to `main`, tags, or manual dispatch. Orchestrates build versioning, Bicep linting, validation, and full infrastructure deployment tests. |
| `lint-and-publish-bicep.yml` | Lints and spellchecks Bicep files to validate code quality. |
| `set-build-variables.yml` | Determines and sets the build version using GitVersion for consistent versioning across deployments. |
| `validate-bicep.yml` | Validates Bicep templates using Azure's `what-if` deployment to ensure correctness before actual deployment. |
| `test-template.yml` | Provisions and tears down Azure infrastructure using `azd`, testing both isolated and public network scenarios. |

## CI/CD Pipeline Flow

1. **Continuous Integration (CI)**
   - Triggered by pull requests to `main`.
   - Runs `lint-and-publish-bicep.yml` to ensure Bicep templates are valid.

2. **Continuous Delivery (CD)**
   - Triggered by pushes to `main`, tags, or manual dispatch.
   - Executes the following sequence:
     - `set-build-variables.yml`: Determines build version.
     - `lint-and-publish-bicep.yml`: Lints and spellchecks Bicep templates.
     - `validate-bicep.yml`: Validates infrastructure templates using Azure's `what-if` operation.
     - `test-template.yml`: Deploys and deletes infrastructure in both network-isolated and public modes to verify end-to-end deployment.

## Best Practices

- **Security:** Uses Azure federated credentials for authentication, minimizing secrets exposure.
- **Operational Excellence:** Automated validation and testing of infrastructure changes before deployment.
- **Performance & Reliability:** Parallel testing of different deployment scenarios (isolated/public) ensures robustness.
- **Cost Optimization:** Automated teardown of test environments prevents resource sprawl.

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Azure Bicep Documentation](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/)
- [Azure Developer CLI (azd)](https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/)

---
For details on each workflow, see the corresponding YAML files in `.github/workflows/`.
