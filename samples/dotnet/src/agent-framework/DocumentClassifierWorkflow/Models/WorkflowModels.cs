// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace DocumentClassifierWorkflow.Models;

/// <summary>
/// Input model for the document classification workflow.
/// Contains the document content and associated classifiers.
/// </summary>
/// <param name="Document">The document content to classify.</param>
/// <param name="Classifiers">List of classifiers to apply to the document.</param>
public sealed record WorkflowInput(
    string Document,
    IReadOnlyList<ClassifierInfo> Classifiers);

/// <summary>
/// Represents a classifier with its name and type.
/// </summary>
/// <param name="Name">The classifier name (e.g., "pi", "content type", "document type").</param>
/// <param name="Type">The classifier type category.</param>
public sealed record ClassifierInfo(
    string Name,
    string Type);

/// <summary>
/// Defines the route path based on classifier analysis.
/// </summary>
[JsonConverter(typeof(JsonStringEnumConverter))]
public enum RoutePath
{
    /// <summary>Route to PI (Personally Identifiable) path.</summary>
    PI,
    /// <summary>Route to Content Type path.</summary>
    ContentType,
    /// <summary>Route to Standard LLM task path.</summary>
    Standard
}

/// <summary>
/// Routing decision from the PreparePrompt executor.
/// </summary>
/// <param name="Input">The original workflow input.</param>
/// <param name="Path">The determined routing path.</param>
public sealed record RoutingDecision(
    WorkflowInput Input,
    RoutePath Path);

/// <summary>
/// Result from the Azure PI Service executor.
/// </summary>
/// <param name="Input">The original workflow input.</param>
/// <param name="PIDetected">Whether personally identifiable information was detected.</param>
/// <param name="PICategories">Categories of PI detected.</param>
/// <param name="Downstream">Downstream processing recommendations.</param>
public sealed record PIServiceResult(
    WorkflowInput Input,
    bool PIDetected,
    IReadOnlyList<string> PICategories,
    string Downstream);

/// <summary>
/// Result from the SuggestContentType LLM executor.
/// </summary>
/// <param name="Input">The original workflow input.</param>
/// <param name="SuggestedContentType">The suggested content type.</param>
/// <param name="Confidence">Confidence score for the suggestion.</param>
public sealed record ContentTypeSuggestion(
    WorkflowInput Input,
    string SuggestedContentType,
    double Confidence);

/// <summary>
/// Result from the GenericIdentification LLM executor.
/// </summary>
/// <param name="Input">The original workflow input.</param>
/// <param name="IdentifiedType">The identified document type.</param>
/// <param name="Schema">Schema information for the document.</param>
/// <param name="Metadata">Additional metadata.</param>
public sealed record GenericIdentificationResult(
    WorkflowInput Input,
    string IdentifiedType,
    string Schema,
    IDictionary<string, string> Metadata);

/// <summary>
/// Unified payload after merging parallel execution results.
/// </summary>
/// <param name="Input">The original workflow input.</param>
/// <param name="CandidateResponses">Candidate classification responses.</param>
/// <param name="SuggestionOutput">Content type suggestion output.</param>
/// <param name="PIResult">PI service result (may be null if not applicable).</param>
/// <param name="GenericResult">Generic identification result (may be null if not applicable).</param>
public sealed record UnifiedPayload(
    WorkflowInput Input,
    IReadOnlyList<CandidateResponse> CandidateResponses,
    ContentTypeSuggestion? SuggestionOutput,
    PIServiceResult? PIResult,
    GenericIdentificationResult? GenericResult);

/// <summary>
/// A candidate response for classification.
/// </summary>
/// <param name="Type">The classification type.</param>
/// <param name="Confidence">Confidence score.</param>
/// <param name="Source">Source of the classification.</param>
public sealed record CandidateResponse(
    string Type,
    double Confidence,
    string Source);

/// <summary>
/// Result from the Encompass5 search executor.
/// </summary>
/// <param name="Payload">The unified payload.</param>
/// <param name="MatchFound">Whether a match was found.</param>
/// <param name="MatchedTerm">The matched term if found.</param>
/// <param name="MatchType">Type of match (heart/variant/synonym).</param>
public sealed record SearchResult(
    UnifiedPayload Payload,
    bool MatchFound,
    string? MatchedTerm,
    string? MatchType);

/// <summary>
/// Decision type from the rationalizer.
/// </summary>
[JsonConverter(typeof(JsonStringEnumConverter))]
public enum RationalizerDecision
{
    /// <summary>Create a new classification.</summary>
    CREATE_NEW,
    /// <summary>Map to an existing classification.</summary>
    MAP,
    /// <summary>Map as a variant of an existing classification.</summary>
    MAP_AS_VARIANT
}

/// <summary>
/// Input for the rationalizer LLM executors.
/// </summary>
/// <param name="Payload">The unified payload.</param>
/// <param name="SearchResult">The search result.</param>
public sealed record RationalizerInput(
    UnifiedPayload Payload,
    SearchResult SearchResult);

/// <summary>
/// Output from a rationalizer LLM executor.
/// </summary>
/// <param name="Decision">The rationalization decision.</param>
/// <param name="MappingTarget">Target for mapping if applicable.</param>
/// <param name="NewTypeName">New type name if creating new.</param>
/// <param name="Reasoning">Explanation for the decision.</param>
/// <param name="Source">Which rationalizer produced this (Generic or ContentType).</param>
public sealed record RationalizerOutput(
    RationalizerDecision Decision,
    string? MappingTarget,
    string? NewTypeName,
    string Reasoning,
    string Source);

/// <summary>
/// Combined outputs from both rationalizers.
/// </summary>
/// <param name="GenericOutput">Output from the generic rationalizer.</param>
/// <param name="ContentTypeOutput">Output from the content type rationalizer.</param>
public sealed record CombinedRationalizerOutput(
    RationalizerOutput GenericOutput,
    RationalizerOutput ContentTypeOutput);

/// <summary>
/// Final workflow output containing candidate responses.
/// </summary>
/// <param name="CandidateResponses">The final candidate responses.</param>
/// <param name="SelectedRationalizer">Which rationalizer was selected (if applicable).</param>
/// <param name="FinalDecision">The final rationalization decision.</param>
public sealed record WorkflowOutput(
    IReadOnlyList<CandidateResponse> CandidateResponses,
    string? SelectedRationalizer,
    RationalizerDecision? FinalDecision);
