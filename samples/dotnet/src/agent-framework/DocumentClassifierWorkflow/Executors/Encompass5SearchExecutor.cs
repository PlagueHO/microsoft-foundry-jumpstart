// Copyright (c) Microsoft. All rights reserved.

using DocumentClassifierWorkflow.Models;
using Microsoft.Agents.AI.Workflows;
using Microsoft.Agents.AI.Workflows.Reflection;

namespace DocumentClassifierWorkflow.Executors;

/// <summary>
/// Encompass5 Search executor that performs heart/variant/synonym matching
/// against the content type suggestion.
/// </summary>
internal sealed class Encompass5SearchExecutor() :
    ReflectingExecutor<Encompass5SearchExecutor>("Encompass5SearchExecutor"),
    IMessageHandler<UnifiedPayload>
{
    /// <summary>
    /// Known content types and their variants/synonyms for matching.
    /// </summary>
    private static readonly Dictionary<string, HashSet<string>> ContentTypeVariants = new(StringComparer.OrdinalIgnoreCase)
    {
        ["Legal Contract"] = ["Agreement", "Contract", "Legal Agreement", "Binding Agreement", "Terms"],
        ["Financial Report"] = ["Annual Report", "Quarterly Report", "Financial Statement", "Earnings Report", "Fiscal Report"],
        ["Technical Documentation"] = ["Tech Doc", "API Documentation", "Developer Guide", "Technical Manual", "Spec"],
        ["Invoice"] = ["Bill", "Statement", "Payment Request", "Receipt"],
        ["Medical Record"] = ["Patient Record", "Clinical Record", "Health Record", "Medical Chart"],
        ["Resume"] = ["CV", "Curriculum Vitae", "Bio", "Professional Profile"],
        ["Policy Document"] = ["Policy", "Procedure", "Guidelines", "Standard Operating Procedure", "SOP"],
        ["Marketing Material"] = ["Brochure", "Flyer", "Advertisement", "Promotional Material"]
    };

    /// <summary>
    /// Performs heart/variant/synonym search against the content type suggestion.
    /// </summary>
    /// <param name="payload">The unified payload from ProcessOutput.</param>
    /// <param name="context">Workflow context for sending messages.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>A task representing the asynchronous operation.</returns>
    public async ValueTask HandleAsync(
        UnifiedPayload payload,
        IWorkflowContext context,
        CancellationToken cancellationToken = default)
    {
        string? matchedTerm = null;
        string? matchType = null;
        bool matchFound = false;

        if (payload.SuggestionOutput is not null)
        {
            var suggestedType = payload.SuggestionOutput.SuggestedContentType;
            (matchFound, matchedTerm, matchType) = FindMatch(suggestedType);
        }

        var searchResult = new SearchResult(
            Payload: payload,
            MatchFound: matchFound,
            MatchedTerm: matchedTerm,
            MatchType: matchType);

        await context.SendMessageAsync(searchResult, cancellationToken).ConfigureAwait(false);
    }

    private static (bool Found, string? Term, string? Type) FindMatch(string suggestedType)
    {
        // Check for exact heart match
        if (ContentTypeVariants.ContainsKey(suggestedType))
        {
            return (true, suggestedType, "heart");
        }

        // Check for variant/synonym matches
        foreach (var (heartType, variants) in ContentTypeVariants)
        {
            // Check if suggested type is a variant
            if (variants.Contains(suggestedType))
            {
                return (true, heartType, "variant");
            }

            // Check for partial synonym matches
            foreach (var variant in variants)
            {
                if (suggestedType.Contains(variant, StringComparison.OrdinalIgnoreCase) ||
                    variant.Contains(suggestedType, StringComparison.OrdinalIgnoreCase))
                {
                    return (true, heartType, "synonym");
                }
            }

            // Check if heart type partially matches
            if (heartType.Contains(suggestedType, StringComparison.OrdinalIgnoreCase) ||
                suggestedType.Contains(heartType, StringComparison.OrdinalIgnoreCase))
            {
                return (true, heartType, "synonym");
            }
        }

        return (false, null, null);
    }
}
