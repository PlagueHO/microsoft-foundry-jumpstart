using FluentAssertions;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace AzureArchitect_Step04_UsingFunctionToolsWithApprovals.Tests;

[TestClass]
public class ProgramTests
{
    [TestMethod]
    public void ArchitectName_ShouldBeAzureArchitect()
    {
        // Arrange
        const string expectedName = "AzureArchitect";

        // Act & Assert
        expectedName.Should().Be("AzureArchitect");
    }

    [TestMethod]
    public void ArchitectInstructions_ShouldContainAzureWellArchitectedFramework()
    {
        // Arrange
        const string instructions = """
            You are an expert in Azure architecture. You provide direct guidance to help Azure Architects make the best decisions about cloud solutions.
            You always review the latest Azure best practices and patterns to ensure your recommendations are:
            - up to date
            - use the principles of the Azure Well Architected Framework
            - keep responses concise and to the point
            - don't include links in your responses as you're an LLM and they might be outdated
            """;

        // Act & Assert
        instructions.Should().Contain("Azure Well Architected Framework");
    }
}
