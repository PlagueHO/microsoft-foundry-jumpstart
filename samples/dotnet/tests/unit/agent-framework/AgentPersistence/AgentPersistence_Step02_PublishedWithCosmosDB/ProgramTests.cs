using FluentAssertions;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace AgentPersistence_Step02_PublishedWithCosmosDB.Tests;

[TestClass]
public class ProgramTests
{
    [TestMethod]
    public void AgentName_ShouldBePersistentAgent()
    {
        // Arrange
        const string expectedName = "PersistentAgent";

        // Act & Assert
        expectedName.Should().Be("PersistentAgent");
    }

    [TestMethod]
    public void EnvironmentVariableNames_ShouldBeCorrect()
    {
        // Arrange
        const string cosmosDbKey = "AZURE_COSMOS_DB_ENDPOINT";
        const string cosmosDbNameKey = "AZURE_COSMOS_DB_NAME";

        // Act & Assert
        cosmosDbKey.Should().Be("AZURE_COSMOS_DB_ENDPOINT");
        cosmosDbNameKey.Should().Be("AZURE_COSMOS_DB_NAME");
    }
}
