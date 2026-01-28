using FluentAssertions;
using HomeLoanAgent;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace HomeLoanAgent.Tests;

[TestClass]
public class ProgramTests
{
    [TestMethod]
    [TestCategory("Unit")]
    public void Options_Question_ShouldBeInitializedAsEmpty()
    {
        // Arrange & Act
        var options = new Options();

        // Assert
        options.Question.Should().BeEmpty();
    }

    [TestMethod]
    [TestCategory("Unit")]
    public void Options_InteractiveMode_ShouldDefaultToFalse()
    {
        // Arrange & Act
        var options = new Options();

        // Assert
        options.Interactive.Should().BeFalse();
    }

    [TestMethod]
    [TestCategory("Unit")]
    public void Options_Question_ShouldBeSettable()
    {
        // Arrange
        var options = new Options();
        const string testQuestion = "Test question";

        // Act
        options.Question = testQuestion;

        // Assert
        options.Question.Should().Be(testQuestion);
    }
}
