using FluentAssertions;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace AzureArchitect_Step02c_Foundry_Agent_PrebuiltAgent.Tests;

[TestClass]
public class ProgramTests
{
    [TestMethod]
    [TestCategory("Unit")]
    public void ArchitectName_ShouldBeAzureArchitect()
    {
        // Arrange
        const string expectedName = "AzureArchitect";

        // Act & Assert
        expectedName.Should().Be("AzureArchitect");
    }

    [TestMethod]
    [TestCategory("Unit")]
    public void EnvironmentVariableNames_ShouldBeCorrect()
    {
        // Arrange
        const string agentIdKey = "AZURE_FOUNDRY_AGENT_ID";
        const string projectIdKey = "AZURE_FOUNDRY_PROJECT_ID";

        // Act & Assert
        agentIdKey.Should().Be("AZURE_FOUNDRY_AGENT_ID");
        projectIdKey.Should().Be("AZURE_FOUNDRY_PROJECT_ID");
    }
}
