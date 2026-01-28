// Copyright (c) Microsoft. All rights reserved.

using DocumentClassifierWorkflow.Models;
using Microsoft.Agents.AI.Workflows;
using Microsoft.Agents.AI.Workflows.Reflection;

namespace DocumentClassifierWorkflow.Executors;

/// <summary>
/// PreparePrompt / Routing executor that determines the processing path
/// based on classifier names in the input.
/// Routes to: PI path, Content Type path, or Standard LLM task path.
/// </summary>
internal sealed class PreparePromptExecutor() :
    ReflectingExecutor<PreparePromptExecutor>("PreparePromptExecutor"),
    IMessageHandler<WorkflowInput>
{
    /// <summary>
    /// Analyzes classifier names and routes to the appropriate processing path.
    /// - If classifier name contains "pi" → PI path
    /// - If contains "content type" / "document type" → Content Type path
    /// - Else → Standard LLM task path
    /// </summary>
    /// <param name="input">The workflow input containing document and classifiers.</param>
    /// <param name="context">Workflow context for sending messages.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>A task representing the asynchronous operation.</returns>
    public async ValueTask HandleAsync(
        WorkflowInput input,
        IWorkflowContext context,
        CancellationToken cancellationToken = default)
    {
        var path = DetermineRoutePath(input.Classifiers);
        var routingDecision = new RoutingDecision(input, path);

        // Send the routing decision to the next executor(s)
        await context.SendMessageAsync(routingDecision, cancellationToken).ConfigureAwait(false);
    }

    private static RoutePath DetermineRoutePath(IReadOnlyList<ClassifierInfo> classifiers)
    {
        foreach (var classifier in classifiers)
        {
            var name = classifier.Name.ToLowerInvariant();

            if (name.Contains("pi", StringComparison.OrdinalIgnoreCase))
            {
                return RoutePath.PI;
            }

            if (name.Contains("content type", StringComparison.OrdinalIgnoreCase) ||
                name.Contains("document type", StringComparison.OrdinalIgnoreCase))
            {
                return RoutePath.ContentType;
            }
        }

        return RoutePath.Standard;
    }
}
