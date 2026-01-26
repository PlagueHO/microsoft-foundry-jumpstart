// Copyright (c) Microsoft. All rights reserved.

// This sample demonstrates how to use a ChatClientAgent with function tools that require a human in the loop for approvals.
// It shows both non-streaming and streaming agent interactions using menu-related tools.
// If the agent is hosted in a service, with a remote user, combine this sample with the Persisted Conversations sample to persist the chat history
// while the agent is waiting for user input.

using System.ComponentModel;
using Azure.AI.OpenAI;
using Azure.Identity;
using Microsoft.Agents.AI;
using Microsoft.Extensions.AI;
using OpenAI;

var endpoint = Environment.GetEnvironmentVariable("AZURE_OPENAI_ENDPOINT") ?? throw new InvalidOperationException("AZURE_OPENAI_ENDPOINT is not set.");
var deploymentName = Environment.GetEnvironmentVariable("AZURE_OPENAI_DEPLOYMENT_NAME") ?? "gpt-5-mini";

const string ArchitectName = "AzureArchitect";
const string ArchitectInstructions = """
You are an expert in Azure architecture. You provide direct guidance to help Azure Architects make the best decisions about cloud solutions.
You always review the latest Azure best practices and patterns to ensure your recommendations are:
- up to date
- use the principles of the Azure Well Architected Framework
- keep responses concise and to the point
- you will use SLO calculator tool whenever asked about reliability or availability
""";

// Create a sample function tool that the agent can use.
[Description("Calculate the composite availability SLO given individual service availabilities (0-1 range).")]
static string CalculateCompositeSlo([Description("Availability values for each dependent service expressed as decimals between 0 and 1.")] double[] availabilities)
{
    if (availabilities is null || availabilities.Length == 0)
    {
        throw new ArgumentException("At least one availability value is required.", nameof(availabilities));
    }

    double composite = availabilities.Aggregate(1.0, (current, availability) => current * availability);
    return $"Composite availability: {composite:P3}";
}

// Create the chat client and agent.
// Note that we are wrapping the function tool with ApprovalRequiredAIFunction to require user approval before invoking it.
AIAgent agent = new AzureOpenAIClient(
    new Uri(endpoint),
    new AzureCliCredential())
     .GetChatClient(deploymentName)
     .CreateAIAgent(
        instructions: ArchitectInstructions,
        name: ArchitectName,
#pragma warning disable MEAI001 // ApprovalRequiredAIFunction is experimental
        tools: [new ApprovalRequiredAIFunction(AIFunctionFactory.Create(CalculateCompositeSlo))]);
#pragma warning restore MEAI001

// Call the agent and check if there are any user input requests to handle.
AgentThread thread = agent.GetNewThread();
var response = await agent.RunAsync("""
    I have service dependencies with availability 0.999, 0.995, and 0.998.
    Calculate the composite SLO and advise how to reach three nines.
    """, thread);
var userInputRequests = response.UserInputRequests.ToList();

// For streaming use:
// var updates = await agent.RunStreamingAsync("Calculate the composite availability for 0.999, 0.995, and 0.998.", thread).ToListAsync();
// userInputRequests = updates.SelectMany(x => x.UserInputRequests).ToList();

while (userInputRequests.Count > 0)
{
    // Ask the user to approve each function call request.
    // For simplicity, we are assuming here that only function approval requests are being made.
#pragma warning disable MEAI001 // FunctionApprovalRequestContent is experimental
    var userInputResponses = userInputRequests
        .OfType<FunctionApprovalRequestContent>()
        .Select(functionApprovalRequest =>
        {
            Console.WriteLine($"The agent would like to invoke the following function, please reply Y to approve: Name {functionApprovalRequest.FunctionCall.Name}");
            return new ChatMessage(ChatRole.User, [functionApprovalRequest.CreateResponse(Console.ReadLine()?.Equals("Y", StringComparison.OrdinalIgnoreCase) ?? false)]);
        })
        .ToList();
#pragma warning restore MEAI001

    // Pass the user input responses back to the agent for further processing.
    response = await agent.RunAsync(userInputResponses, thread);

    userInputRequests = response.UserInputRequests.ToList();

    // For streaming use:
    // updates = await agent.RunStreamingAsync(userInputResponses, thread).ToListAsync();
    // userInputRequests = updates.SelectMany(x => x.UserInputRequests).ToList();
}

Console.WriteLine($"\nAgent: {response}");

// For streaming use:
// Console.WriteLine($"\nAgent: {updates.ToAgentRunResponse()}");
