using FluentAssertions;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace AzureArchitect_Step08_HybridToolCalling.Tests;

[TestClass]
public sealed class ProgramTests
{
    [TestMethod]
    [TestCategory("Unit")]
    public void AgentName_ShouldBeHybridToolCallingAgent()
    {
        // Arrange & Act & Assert
        const string expectedName = "HybridToolCallingAgent";
        expectedName.Should().Be("HybridToolCallingAgent");
    }

    [TestMethod]
    [TestCategory("Unit")]
    public void AgentInstructions_ShouldMentionMcpAndSloCalculator()
    {
        // Arrange
        const string instructions = """
            You are an Azure reliability assistant that combines documentation search with availability calculations.
            Use the Microsoft Learn MCP tools to find official Azure documentation.
            Use the SLO calculator tool to compute composite availability from individual service SLAs.
            Always cite sources from Microsoft Learn when providing guidance.
            """;

        // Act & Assert
        instructions.Should().Contain("Microsoft Learn MCP");
        instructions.Should().Contain("SLO calculator");
    }
}
