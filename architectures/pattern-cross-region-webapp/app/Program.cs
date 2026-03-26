// Copyright (c) Microsoft. All rights reserved.

using Azure.AI.Projects;
using Azure.Identity;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddRazorPages();

// Register the AIProjectClient as a singleton using managed identity
builder.Services.AddSingleton(_ =>
{
    var endpoint = builder.Configuration["AZURE_FOUNDRY_PROJECT_ENDPOINT"]
        ?? throw new InvalidOperationException("AZURE_FOUNDRY_PROJECT_ENDPOINT is not configured.");

    return new AIProjectClient(new Uri(endpoint), new DefaultAzureCredential());
});

var app = builder.Build();

if (!app.Environment.IsDevelopment())
{
    app.UseHsts();
}

app.UseHttpsRedirection();
app.UseStaticFiles();
app.UseRouting();
app.MapRazorPages();

app.Run();
