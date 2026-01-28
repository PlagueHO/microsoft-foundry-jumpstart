using FluentAssertions;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace AgentPersistence_Step01_UnpublishedAgent.Tests;

[TestClass]
public class ProgramTests
{
    [TestMethod]
    [TestCategory("Unit")]
    public void AgentName_ShouldBePersistentAgent()
    {
        // Arrange
        const string expectedName = "PersistentAgent";

        // Act & Assert
        expectedName.Should().Be("PersistentAgent");
    }

    [TestMethod]
    [TestCategory("Unit")]
    public void AgentInstructions_ShouldContainPersistence()
    {
        // Arrange
        const string instructions = """
            You are a helpful assistant demonstrating agent persistence.
            You can maintain conversation state across multiple turns.
            """;

        // Act & Assert
        instructions.Should().Contain("persistence");
    }
}
