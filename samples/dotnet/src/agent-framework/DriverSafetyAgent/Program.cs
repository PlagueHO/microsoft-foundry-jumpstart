// Copyright (c) Microsoft. All rights reserved.

// This sample demonstrates a vehicle telematics driver safety recommendations agent
// using Microsoft Agent Framework with a Responses Agent backed by an LLM in Microsoft Foundry.
// The agent analyzes driving telemetry data and provides safety recommendations.

using Azure.AI.Projects;
using Azure.Identity;
using Microsoft.Agents.AI;

string endpoint = Environment.GetEnvironmentVariable("AZURE_FOUNDRY_PROJECT_ENDPOINT")
    ?? throw new InvalidOperationException("AZURE_FOUNDRY_PROJECT_ENDPOINT is not set.");
string deploymentName = Environment.GetEnvironmentVariable("AZURE_FOUNDRY_PROJECT_DEPLOYMENT_NAME")
    ?? "gpt-4o-mini";

const string AgentName = "DriverSafetyAdvisor";
const string AgentInstructions = """
    You are a vehicle telematics driver safety recommendations agent.
    You analyze driving telemetry data and provide actionable safety recommendations to improve driver behavior.

    Your expertise includes:
    - Analyzing speed, acceleration, braking, and cornering patterns
    - Identifying risky driving behaviors such as harsh braking, rapid acceleration, and aggressive cornering
    - Evaluating driver fatigue indicators based on time-of-day and trip duration
    - Assessing environmental risk factors like weather conditions, road types, and traffic density
    - Providing a driver safety score (0-100) based on the telemetry data provided
    - Recommending specific, actionable improvements to reduce accident risk

    When analyzing telemetry data, always:
    1. Summarize the key safety metrics
    2. Identify the top risk factors
    3. Provide a driver safety score with justification
    4. Give prioritized, actionable recommendations
    5. Keep responses concise and focused on safety outcomes
    """;

// Create a Responses Agent backed by an LLM in Microsoft Foundry.
// This is code-first and does not create a server-managed agent resource.
AIAgent agent = new AIProjectClient(
    new Uri(endpoint),
    new AzureCliCredential())
        .AsAIAgent(
            model: deploymentName,
            name: AgentName,
            instructions: AgentInstructions);

// Create a session to maintain conversation context across multiple turns.
AgentSession session = await agent.CreateSessionAsync();

// --- Turn 1: Analyze a sample telemetry snapshot ---
Console.WriteLine("=== Vehicle Telematics Driver Safety Agent ===\n");
Console.WriteLine("--- Analyzing trip telemetry data ---\n");

string telemetryPrompt = """
    Analyze the following vehicle telematics data from a recent trip and provide safety recommendations:

    Trip Summary:
    - Duration: 47 minutes
    - Distance: 32.4 km
    - Average Speed: 68 km/h
    - Max Speed: 112 km/h (in a 100 km/h zone)
    - Time of Day: 11:30 PM (night driving)

    Events Detected:
    - Harsh braking events: 5 (threshold: >0.45g deceleration)
    - Rapid acceleration events: 3 (threshold: >0.35g acceleration)
    - Sharp cornering events: 2 (threshold: >0.3g lateral force)
    - Phone usage detected: 2 instances (total 1 min 45 sec)
    - Seatbelt unfastened alert: 0
    - Lane departure warnings: 4

    Speed Profile:
    - Time over speed limit: 6 minutes 12 seconds
    - Speeding severity: up to 12 km/h over limit

    Environmental Conditions:
    - Weather: Light rain
    - Road type: Mixed urban/highway
    - Traffic density: Moderate
    """;

await foreach (AgentResponseUpdate update in agent.RunStreamingAsync(telemetryPrompt, session))
{
    Console.Write(update);
}

Console.WriteLine("\n\n-------------------\n");

// --- Turn 2: Follow-up asking for a comparison with fleet averages ---
Console.WriteLine("--- Requesting fleet comparison ---\n");

await foreach (AgentResponseUpdate update in agent.RunStreamingAsync("""
    Based on the trip you just analyzed, how would this driver compare to typical fleet averages?
    Assume fleet averages are:
    - Harsh braking: 1.2 events per trip
    - Rapid acceleration: 0.8 events per trip
    - Phone usage: 0.3 instances per trip
    - Average driver safety score: 78/100

    What specific coaching plan would you recommend for this driver over the next 30 days?
    """, session))
{
    Console.Write(update);
}

Console.WriteLine("\n\n-------------------\n");

// --- Turn 3: Ask about long-term risk ---
Console.WriteLine("--- Assessing long-term risk profile ---\n");

await foreach (AgentResponseUpdate update in agent.RunStreamingAsync("""
    If this driving pattern continues unchanged over the next 12 months (approximately 500 similar trips),
    what are the projected safety implications? Consider:
    - Estimated accident probability increase
    - Vehicle wear and tear impact (brakes, tires, suspension)
    - Insurance risk category implications
    - Fuel efficiency impact from aggressive driving behaviors
    """, session))
{
    Console.Write(update);
}

Console.WriteLine("\n");
