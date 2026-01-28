// Copyright (c) Microsoft. All rights reserved.

using Azure.AI.OpenAI;
using Azure.Identity;
using DocumentClassifierWorkflow.Executors;
using DocumentClassifierWorkflow.Models;
using Microsoft.Agents.AI.Workflows;
using Microsoft.Extensions.AI;

namespace DocumentClassifierWorkflow;

/// <summary>
/// Document Classifier Workflow using Microsoft Agent Framework.
///
/// This workflow implements a document classification pipeline that:
/// 1. Routes based on classifier type (PI, ContentType, or Standard)
/// 2. Executes parallel classification using Azure PI Service, ContentType LLM, and Generic LLM
/// 3. Merges results and searches for existing type matches
/// 4. If no match found, runs rationalization to decide CREATE_NEW, MAP, or MAP_AS_VARIANT
/// 5. Assembles and outputs final classification candidates
/// </summary>
/// <remarks>
/// Architecture based on the MAML workflow pattern:
/// - PreparePrompt/Routing → Parallel Execution → ProcessOutput/Merge
/// - Encompass5 Search → Match Decision
/// - If match: emit candidate and stop
/// - If no match: Rationalizer path with Generic + ContentType rationalisers
/// </remarks>
public static class Program
{
    /// <summary>
    /// Main entry point for the workflow.
    /// </summary>
    public static async Task Main()
    {
        Console.WriteLine("Document Classifier Workflow - Microsoft Agent Framework");
        Console.WriteLine("=".PadRight(60, '='));

        // Initialize optional LLM client (set environment variables to enable)
        var chatClient = InitializeChatClient();

        // Create all executors
        var preparePrompt = new PreparePromptExecutor();
        var azurePIService = new AzurePIServiceExecutor();
        var suggestContentType = new SuggestContentTypeExecutor(chatClient);
        var genericIdentification = new GenericIdentificationExecutor(chatClient);
        var processOutput = new ProcessOutputExecutor();
        var encompass5Search = new Encompass5SearchExecutor();
        var matchDecision = new MatchDecisionExecutor();
        var parseRationalizerInput = new ParseRationalizerInputExecutor();
        var genericRationalizer = new GenericRationalizerExecutor(chatClient);
        var contentTypeRationalizer = new ContentTypeRationalizerExecutor(chatClient);
        var parseRationalizerOutput = new ParseRationalizerOutputExecutor();
        var selectRationalizerOutput = new SelectRationalizerOutputExecutor();
        var assembleOutput = new AssembleOutputExecutor();

        // Build the workflow graph
        var workflow = BuildWorkflow(
            preparePrompt,
            azurePIService,
            suggestContentType,
            genericIdentification,
            processOutput,
            encompass5Search,
            matchDecision,
            parseRationalizerInput,
            genericRationalizer,
            contentTypeRationalizer,
            parseRationalizerOutput,
            selectRationalizerOutput,
            assembleOutput);

        // Sample documents for testing
        var testDocuments = GetSampleDocuments();

        foreach (var (document, classifiers, description) in testDocuments)
        {
            Console.WriteLine();
            Console.WriteLine($"Processing: {description}");
            Console.WriteLine("-".PadRight(50, '-'));

            var input = new WorkflowInput(document, classifiers);

            try
            {
                StreamingRun run = await InProcessExecution.StreamAsync(workflow, input)
                    .ConfigureAwait(false);

                await foreach (WorkflowEvent evt in run.WatchStreamAsync().ConfigureAwait(false))
                {
                    if (evt is WorkflowOutputEvent outputEvt && outputEvt.Data is WorkflowOutput result)
                    {
                        Console.WriteLine();
                        Console.WriteLine("  [RESULT] Classification Output:");
                        Console.WriteLine($"    Selected Rationalizer: {result.SelectedRationalizer ?? "N/A (direct match)"}");
                        Console.WriteLine($"    Final Decision: {result.FinalDecision?.ToString() ?? "Match found"}");
                        Console.WriteLine("    Candidate Responses:");

                        foreach (var candidate in result.CandidateResponses)
                        {
                            Console.WriteLine($"      - Type: {candidate.Type}");
                            Console.WriteLine($"        Confidence: {candidate.Confidence:P0}");
                            Console.WriteLine($"        Source: {candidate.Source}");
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"  [ERROR] {ex.Message}");
            }
        }

        Console.WriteLine();
        Console.WriteLine("=".PadRight(60, '='));
        Console.WriteLine("Workflow completed.");
    }

    private static Workflow BuildWorkflow(
        PreparePromptExecutor preparePrompt,
        AzurePIServiceExecutor azurePIService,
        SuggestContentTypeExecutor suggestContentType,
        GenericIdentificationExecutor genericIdentification,
        ProcessOutputExecutor processOutput,
        Encompass5SearchExecutor encompass5Search,
        MatchDecisionExecutor matchDecision,
        ParseRationalizerInputExecutor parseRationalizerInput,
        GenericRationalizerExecutor genericRationalizer,
        ContentTypeRationalizerExecutor contentTypeRationalizer,
        ParseRationalizerOutputExecutor parseRationalizerOutput,
        SelectRationalizerOutputExecutor selectRationalizerOutput,
        AssembleOutputExecutor assembleOutput)
    {
        var builder = new WorkflowBuilder(preparePrompt);

        // Stage 1: PreparePrompt routes to parallel execution
        // Fan-out from PreparePrompt to all three parallel processors
        builder.AddFanOutEdge(
            preparePrompt,
            targets: [azurePIService, suggestContentType, genericIdentification]);

        // Stage 2: Parallel processors fan-in to ProcessOutput/Merge
        builder.AddEdge(azurePIService, processOutput);
        builder.AddEdge(suggestContentType, processOutput);
        builder.AddEdge(genericIdentification, processOutput);

        // Stage 3: ProcessOutput → Encompass5Search → MatchDecision
        builder.AddEdge(processOutput, encompass5Search);
        builder.AddEdge(encompass5Search, matchDecision);

        // Stage 4: MatchDecision either yields output (match found) or continues to rationalizers
        // The MatchDecisionExecutor handles this internally via YieldOutput or SendMessage

        // Stage 5: STANDALONERATIONLISER path (when no match found)
        builder.AddEdge(matchDecision, parseRationalizerInput);

        // Fan-out to both rationalizers
        builder.AddFanOutEdge(
            parseRationalizerInput,
            targets: [genericRationalizer, contentTypeRationalizer]);

        // Both rationalizers fan-in to ParseRationalizerOutput
        builder.AddEdge(genericRationalizer, parseRationalizerOutput);
        builder.AddEdge(contentTypeRationalizer, parseRationalizerOutput);

        // Stage 6: Select and assemble final output
        builder.AddEdge(parseRationalizerOutput, selectRationalizerOutput);
        builder.AddEdge(selectRationalizerOutput, assembleOutput);

        // Mark output sources (MatchDecision yields directly, AssembleOutput is the final step)
        builder.WithOutputFrom(matchDecision);
        builder.WithOutputFrom(assembleOutput);

        return builder.Build();
    }

    private static IChatClient? InitializeChatClient()
    {
        var endpoint = Environment.GetEnvironmentVariable("AZURE_OPENAI_ENDPOINT");
        var deploymentName = Environment.GetEnvironmentVariable("AZURE_OPENAI_DEPLOYMENT_NAME");

        if (string.IsNullOrWhiteSpace(endpoint))
        {
            Console.WriteLine("[INFO] AZURE_OPENAI_ENDPOINT not set. Using heuristic-based classification.");
            return null;
        }

        try
        {
            var client = new AzureOpenAIClient(new Uri(endpoint), new AzureCliCredential());
            var chatClient = client.GetChatClient(deploymentName ?? "gpt-4").AsIChatClient();
            Console.WriteLine($"[INFO] Connected to Azure OpenAI at {endpoint}");
            return chatClient;
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[WARN] Failed to initialize Azure OpenAI client: {ex.Message}");
            Console.WriteLine("[INFO] Falling back to heuristic-based classification.");
            return null;
        }
    }

    private static (string Document, List<ClassifierInfo> Classifiers, string Description)[] GetSampleDocuments()
    {
        return
        [
            (
                Document: """
                    SERVICES AGREEMENT

                    This Services Agreement ("Agreement") is entered into as of January 1, 2026,
                    by and between Acme Corporation ("Provider") and XYZ Industries ("Client").

                    WHEREAS, Provider agrees to provide software development services...
                    The parties hereby agree to the following terms and conditions...
                    """,
                Classifiers: [new ClassifierInfo("content type", "category")],
                Description: "Legal Contract (Content Type path)"
            ),
            (
                Document: """
                    Dear John Smith,

                    Your SSN 123-45-6789 has been associated with the following accounts.
                    Please contact us at john.smith@email.com or (555) 123-4567 to verify.

                    Your billing address: 123 Main Street, Anytown, USA
                    Credit Card ending in 4242
                    """,
                Classifiers: [new ClassifierInfo("pi detection", "security")],
                Description: "PI-Sensitive Document (PI path)"
            ),
            (
                Document: """
                    Q4 2025 Financial Report

                    Revenue: $45.2M (+12% YoY)
                    Operating Income: $12.1M
                    Net Income: $8.7M

                    The quarterly results exceeded analyst expectations...
                    Fiscal year guidance remains unchanged at $180M-$190M.
                    """,
                Classifiers: [new ClassifierInfo("document type", "category")],
                Description: "Financial Report (Content Type path)"
            ),
            (
                Document: """
                    Subject: Project Status Update
                    From: manager@company.com
                    To: team@company.com

                    Hi team,

                    I wanted to provide a quick update on our Q1 deliverables.
                    The architecture review is complete and we're on track for launch.

                    Sincerely,
                    Project Manager
                    """,
                Classifiers: [new ClassifierInfo("general", "standard")],
                Description: "Email Document (Standard path)"
            ),
            (
                Document: """
                    TECHNICAL SPECIFICATION v2.1

                    API Endpoint: /api/v2/documents
                    Method: POST
                    Content-Type: application/json

                    This implementation guide covers the REST API architecture
                    for the document classification microservice.
                    """,
                Classifiers: [new ClassifierInfo("content type", "category")],
                Description: "Technical Documentation (Content Type path)"
            )
        ];
    }
}
