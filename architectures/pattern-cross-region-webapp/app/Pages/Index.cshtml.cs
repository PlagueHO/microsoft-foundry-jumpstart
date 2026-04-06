// Copyright (c) Microsoft. All rights reserved.

using Azure.AI.Projects;
using Azure.AI.Projects.OpenAI;
using Microsoft.Agents.AI;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;

namespace CrossRegionAgent.Pages;

public sealed class IndexModel(AIProjectClient aiProjectClient, IConfiguration configuration) : PageModel
{
    [BindProperty]
    public string? Question { get; set; }

    public string? Answer { get; set; }

    public string? ErrorMessage { get; set; }

    public void OnGet()
    {
    }

    public async Task OnPostAsync()
    {
        if (string.IsNullOrWhiteSpace(Question))
        {
            return;
        }

        var deploymentName = configuration["AZURE_FOUNDRY_PROJECT_DEPLOYMENT_NAME"] ?? "gpt-4o";
        var agentName = $"cross-region-agent-{DateTime.UtcNow:yyyyMMdd'T'HHmmss'Z'}";

        const string instructions = """
            You are an expert in Azure architecture. You provide direct guidance to help
            Azure Architects make the best decisions about cloud solutions. Keep responses
            concise and to the point, following Azure Well-Architected Framework principles.
            """;

        try
        {
            AgentVersionCreationOptions options = new(new PromptAgentDefinition(model: deploymentName)
            {
                Instructions = instructions
            });

            AgentVersion agentVersion = aiProjectClient.AgentAdministrationClient.CreateAgentVersion(agentName: agentName, options);
            AIAgent agent = aiProjectClient.GetAIAgent(agentVersion);

            var responseBuilder = new System.Text.StringBuilder();
            await foreach (AgentRunResponseUpdate update in agent.RunStreamingAsync(Question))
            {
                responseBuilder.Append(update);
            }

            Answer = responseBuilder.ToString();

            // Clean up the server-side agent
            await aiProjectClient.AgentAdministrationClient.DeleteAgentAsync(agent.Name);
        }
        catch (Exception ex)
        {
            ErrorMessage = ex.Message;
        }
    }
}
