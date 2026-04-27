using Azure.Core;
using Azure.Identity;
using ImageGenerationExplorer.Components;
using ImageGenerationExplorer.Models;
using ImageGenerationExplorer.Services;
using MudBlazor.Services;

var builder = WebApplication.CreateBuilder(args);

// Suppress noisy JSDisconnectedException warnings from MudBlazor component disposal
// during Blazor Server circuit teardown (known issue with MudBlazor + Blazor Server).
builder.Logging.AddFilter("Microsoft.AspNetCore.Components.Server.Circuits.RemoteRenderer", LogLevel.Error);
builder.Logging.AddFilter("Microsoft.AspNetCore.Components.Server.Circuits.CircuitHost", LogLevel.Critical);

// Add services to the container.
builder.Services.AddRazorComponents()
    .AddInteractiveServerComponents();
builder.Services.AddMudServices();
builder.Services.AddOptions<ImageGenerationExplorerOptions>()
    .BindConfiguration(ImageGenerationExplorerOptions.SectionName)
    .ValidateDataAnnotations()
    .ValidateOnStart();
builder.Services.AddSingleton<TokenCredential>(new DefaultAzureCredential());
builder.Services.AddHttpClient<IImageGenerationProvider, MaiImageGenerationProvider>(client =>
    client.Timeout = TimeSpan.FromMinutes(5));
builder.Services.AddHttpClient<OpenAiImageGenerationProvider>(client =>
    client.Timeout = TimeSpan.FromMinutes(5));
builder.Services.AddSingleton<IImageGenerationProvider>(sp => sp.GetRequiredService<OpenAiImageGenerationProvider>());
builder.Services.AddTransient<ImageComparisonService>();

var app = builder.Build();

// Configure the HTTP request pipeline.
if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Error", createScopeForErrors: true);
    // The default HSTS value is 30 days. You may want to change this for production scenarios, see https://aka.ms/aspnetcore-hsts.
    app.UseHsts();
}

app.UseHttpsRedirection();

app.UseAntiforgery();

app.MapStaticAssets();
app.MapRazorComponents<App>()
    .AddInteractiveServerRenderMode();

app.Run();
