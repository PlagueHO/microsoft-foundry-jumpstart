using MaiImage2Simple.Components;
using MaiImage2Simple.Models;
using MaiImage2Simple.Services;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddRazorComponents()
    .AddInteractiveServerComponents();
builder.Services.AddOptions<MicrosoftFoundryOptions>()
    .BindConfiguration(MicrosoftFoundryOptions.SectionName)
    .ValidateDataAnnotations()
    .Validate(
        options => options.DefaultWidth * options.DefaultHeight <= 1_048_576,
        "MicrosoftFoundry:DefaultWidth * DefaultHeight must be <= 1048576 for MAI-Image-2.")
    .ValidateOnStart();
builder.Services.AddScoped<IMaiImageService, MaiImageService>();

var app = builder.Build();

// Configure the HTTP request pipeline.
if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Error", createScopeForErrors: true);
    // The default HSTS value is 30 days. You may want to change this for production scenarios, see https://aka.ms/aspnetcore-hsts.
    app.UseHsts();
}
app.UseStatusCodePagesWithReExecute("/not-found", createScopeForStatusCodePages: true);
app.UseHttpsRedirection();

app.UseAntiforgery();

app.MapStaticAssets();
app.MapRazorComponents<App>()
    .AddInteractiveServerRenderMode();

app.Run();
