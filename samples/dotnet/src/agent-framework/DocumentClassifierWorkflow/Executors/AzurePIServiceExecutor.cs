// Copyright (c) Microsoft. All rights reserved.

using DocumentClassifierWorkflow.Models;
using Microsoft.Agents.AI.Workflows;
using Microsoft.Agents.AI.Workflows.Reflection;

namespace DocumentClassifierWorkflow.Executors;

/// <summary>
/// Azure PI Service executor that performs a single-pass PI detection scan.
/// Records PI detection results for downstream processing.
/// </summary>
internal sealed class AzurePIServiceExecutor() :
    ReflectingExecutor<AzurePIServiceExecutor>("AzurePIServiceExecutor"),
    IMessageHandler<RoutingDecision>
{
    private static readonly string[] CommonPICategories =
    [
        "SSN",
        "Email",
        "PhoneNumber",
        "CreditCard",
        "Address",
        "DateOfBirth",
        "DriverLicense",
        "Passport"
    ];

    /// <summary>
    /// Performs PI detection on the document content.
    /// </summary>
    /// <param name="decision">The routing decision containing the input.</param>
    /// <param name="context">Workflow context for sending messages.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>A task representing the asynchronous operation.</returns>
    public async ValueTask HandleAsync(
        RoutingDecision decision,
        IWorkflowContext context,
        CancellationToken cancellationToken = default)
    {
        var input = decision.Input;
        var documentContent = input.Document.ToLowerInvariant();

        // Simulate PI detection logic
        var detectedCategories = new List<string>();
        foreach (var category in CommonPICategories)
        {
            if (ContainsPIPattern(documentContent, category))
            {
                detectedCategories.Add(category);
            }
        }

        var result = new PIServiceResult(
            Input: input,
            PIDetected: detectedCategories.Count > 0,
            PICategories: detectedCategories,
            Downstream: detectedCategories.Count > 0
                ? "Redaction recommended before further processing"
                : "No PI detected, proceed normally");

        await context.SendMessageAsync(result, cancellationToken).ConfigureAwait(false);
    }

    private static bool ContainsPIPattern(string content, string category) =>
        category.ToLowerInvariant() switch
        {
            "ssn" => content.Contains("ssn", StringComparison.OrdinalIgnoreCase) ||
                     System.Text.RegularExpressions.Regex.IsMatch(content, @"\d{3}-\d{2}-\d{4}"),
            "email" => content.Contains('@') && content.Contains('.'),
            "phonenumber" => System.Text.RegularExpressions.Regex.IsMatch(content, @"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"),
            "creditcard" => System.Text.RegularExpressions.Regex.IsMatch(content, @"\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}"),
            "address" => content.Contains("street", StringComparison.OrdinalIgnoreCase) ||
                         content.Contains("avenue", StringComparison.OrdinalIgnoreCase) ||
                         content.Contains("blvd", StringComparison.OrdinalIgnoreCase),
            _ => false
        };
}
