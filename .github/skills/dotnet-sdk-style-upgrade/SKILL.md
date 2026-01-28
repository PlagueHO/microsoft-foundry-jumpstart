---
name: dotnet-sdk-style-upgrade
description: Converts legacy .NET project files (.csproj, .fsproj, .vbproj) to modern SDK-style format. Use when asked to modernize, upgrade, migrate, or convert .NET projects, or when encountering non-SDK-style project files that need updating to current .NET standards.
metadata:
  author: microsoft-foundry-jumpstart
  version: "1.0"
  reference: https://learn.microsoft.com/en-us/dotnet/core/project-sdk/overview
---

# Upgrading to SDK-Style Projects

**Required Reference**: Before proceeding, consult the [.NET SDK-style project documentation](https://learn.microsoft.com/en-us/dotnet/core/project-sdk/overview) for authoritative guidance on SDK-style projects.

## SDK Selection Guide

Analyze project files to recommend the appropriate SDK:

| Project Type | SDK | Indicators |
|-------------|-----|------------|
| Console/Library | `Microsoft.NET.Sdk` | No web/UI references |
| ASP.NET Core/Web API | `Microsoft.NET.Sdk.Web` | `Microsoft.AspNetCore.*`, Startup.cs, Controllers |
| Razor Class Library | `Microsoft.NET.Sdk.Razor` | `.razor` files, Razor components |
| Blazor WebAssembly | `Microsoft.NET.Sdk.BlazorWebAssembly` | `Microsoft.AspNetCore.Components.WebAssembly` |
| Worker/Background Service | `Microsoft.NET.Sdk.Worker` | `IHostedService`, BackgroundService |
| WinForms | `Microsoft.NET.Sdk` + `<UseWindowsForms>` | `System.Windows.Forms` |
| WPF | `Microsoft.NET.Sdk` + `<UseWPF>` | `PresentationFramework`, `.xaml` files |
| MSTest | `MSTest.Sdk` | `Microsoft.VisualStudio.TestTools.UnitTesting` |
| .NET Aspire AppHost | `Aspire.AppHost.Sdk` | Aspire orchestration project |

## Analysis Checklist

Before upgrading, analyze and review:

- [ ] **Project type**: Console, library, web, test, desktop, or worker
- [ ] **Target framework**: Current TFM and desired target (e.g., `net9.0`, `net48`)
- [ ] **Package references**: Check `packages.config` or `<Reference>` with HintPath
- [ ] **Assembly references**: GAC or local assemblies that need conversion
- [ ] **Conditional compilation**: `#if` directives, DEBUG/RELEASE configurations
- [ ] **Build configurations**: Custom configurations beyond Debug/Release
- [ ] **Pre/Post build events**: Scripts in `<PreBuildEvent>` or `<PostBuildEvent>`
- [ ] **Custom targets/props**: `.targets` or `.props` file imports
- [ ] **AssemblyInfo.cs**: Attributes to migrate or auto-generate
- [ ] **Resources**: `.resx` files, embedded resources, content files
- [ ] **Project references**: Other projects in solution
- [ ] **COM references**: ActiveX/COM interop dependencies
- [ ] **WCF/ASMX references**: Service references requiring migration
- [ ] **Project GUIDs**: Solution file references (update if changing)
- [ ] **Output paths**: Custom `OutputPath`, `IntermediateOutputPath`
- [ ] **Signing**: Strong name keys, delay signing settings
- [ ] **Platform target**: x86, x64, AnyCPU, ARM settings

## Upgrade Process

1. **Identify SDK**: Analyze references and file patterns to determine SDK
2. **Create minimal project file**:

   ```xml
   <Project Sdk="SELECTED_SDK">
     <PropertyGroup>
       <TargetFramework>net9.0</TargetFramework>
       <Nullable>enable</Nullable>
       <ImplicitUsings>enable</ImplicitUsings>
     </PropertyGroup>
   </Project>
   ```

3. **Add OutputType** if executable: `<OutputType>Exe</OutputType>` or `<OutputType>WinExe</OutputType>`
4. **Migrate PackageReferences**: Convert `packages.config` or HintPath references
5. **Remove redundant elements**: SDK-style auto-includes `*.cs`, `*.resx`, etc.
6. **Add desktop properties** for WinForms/WPF:

   ```xml
   <UseWindowsForms>true</UseWindowsForms>
   <!-- or -->
   <UseWPF>true</UseWPF>
   ```

## Key Differences from Legacy

- No `<Compile Include="**/*.cs" />` needed (auto-included)
- No assembly info file needed (`<GenerateAssemblyInfo>true</GenerateAssemblyInfo>` default)
- PackageReference replaces packages.config
- No ProjectGuid, ProjectTypeGuids required
- No explicit SDK imports needed

## Validation

After upgrade, run:

```bash
dotnet build
dotnet msbuild -preprocess:output.xml  # View expanded project
```
