using System.Net;
using System.Net.Http.Headers;
using System.Text;
using Azure;
using Azure.Core;
using FluentAssertions;
using MaiImage2Simple.Models;
using MaiImage2Simple.Services;
using Microsoft.Extensions.Options;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace MaiImage2Simple.Tests;

[TestClass]
public sealed class MaiImageServiceTests
{
    [TestMethod]
    [TestCategory("Unit")]
    public async Task GenerateImageAsync_ReturnsError_WhenDimensionsAreTooSmall()
    {
        // Arrange
        var handler = new StubHttpMessageHandler((_, _) =>
            throw new InvalidOperationException("HTTP call should not occur."));
        using var httpClient = new HttpClient(handler);
        var service = CreateService(httpClient);

        // Act
        var result = await service.GenerateImageAsync(new MaiImageRequest
        {
            Prompt = "A lighthouse",
            Width = 512,
            Height = 1024,
        });

        // Assert
        result.IsSuccess.Should().BeFalse();
        result.ErrorMessage.Should().Contain("at least 768");
        handler.CallCount.Should().Be(0);
    }

    [TestMethod]
    [TestCategory("Unit")]
    public async Task GenerateImageAsync_ReturnsError_WhenPixelAreaIsTooLarge()
    {
        // Arrange
        var handler = new StubHttpMessageHandler((_, _) =>
            throw new InvalidOperationException("HTTP call should not occur."));
        using var httpClient = new HttpClient(handler);
        var service = CreateService(httpClient);

        // Act
        var result = await service.GenerateImageAsync(new MaiImageRequest
        {
            Prompt = "A mountain",
            Width = 2048,
            Height = 1024,
        });

        // Assert
        result.IsSuccess.Should().BeFalse();
        result.ErrorMessage.Should().Contain("1048576");
        handler.CallCount.Should().Be(0);
    }

    [TestMethod]
    [TestCategory("Unit")]
    public async Task GenerateImageAsync_ReturnsBase64_WhenApiReturnsImageData()
    {
        // Arrange
        const string expectedBase64 = "c2FtcGxlLWltYWdl";
        var handler = new StubHttpMessageHandler((request, _) =>
        {
            request.RequestUri.Should().NotBeNull();
            request.RequestUri!.AbsolutePath.Should().Be("/mai/v1/images/generations");
            request.Headers.Authorization.Should().BeEquivalentTo(
                new AuthenticationHeaderValue("Bearer", "fake-token"));

            var content = "{\"data\":[{\"b64_json\":\"c2FtcGxlLWltYWdl\"}]}";
            return Task.FromResult(new HttpResponseMessage(HttpStatusCode.OK)
            {
                Content = new StringContent(content, Encoding.UTF8, "application/json"),
            });
        });

        using var httpClient = new HttpClient(handler);
        var service = CreateService(httpClient);

        // Act
        var result = await service.GenerateImageAsync(new MaiImageRequest
        {
            Prompt = "A tree",
            Width = 1024,
            Height = 1024,
        });

        // Assert
        result.IsSuccess.Should().BeTrue();
        result.Base64Image.Should().Be(expectedBase64);
        result.ErrorMessage.Should().BeNull();
        handler.CallCount.Should().Be(1);
    }

    [TestMethod]
    [TestCategory("Unit")]
    public async Task GenerateImageAsync_MapsApiErrorMessage_WhenRequestFails()
    {
        // Arrange
        var handler = new StubHttpMessageHandler((_, _) =>
        {
            var content =
                "{\"error\":{\"message\":\"Deployment not ready\",\"code\":\"BadRequest\"}}";
            return Task.FromResult(new HttpResponseMessage(HttpStatusCode.BadRequest)
            {
                Content = new StringContent(content, Encoding.UTF8, "application/json"),
            });
        });

        using var httpClient = new HttpClient(handler);
        var service = CreateService(httpClient);

        // Act
        var result = await service.GenerateImageAsync(new MaiImageRequest
        {
            Prompt = "A city",
            Width = 1024,
            Height = 1024,
        });

        // Assert
        result.IsSuccess.Should().BeFalse();
        result.StatusCode.Should().Be((int)HttpStatusCode.BadRequest);
        result.ErrorMessage.Should().Contain("Deployment not ready")
            .And.Contain("BadRequest");
        handler.CallCount.Should().Be(1);
    }

    private static MaiImageService CreateService(HttpClient httpClient)
    {
        var options = Options.Create(new MicrosoftFoundryOptions
        {
            ResourceEndpoint = "https://example.services.ai.azure.com",
            ImageDeployment = "mai-image-2",
            DefaultWidth = 1024,
            DefaultHeight = 1024,
        });

        return new MaiImageService(httpClient, options, new FakeTokenCredential());
    }

    private sealed class FakeTokenCredential : TokenCredential
    {
        public override AccessToken GetToken(
            TokenRequestContext requestContext,
            CancellationToken cancellationToken)
        {
            return new AccessToken("fake-token", DateTimeOffset.UtcNow.AddMinutes(5));
        }

        public override ValueTask<AccessToken> GetTokenAsync(
            TokenRequestContext requestContext,
            CancellationToken cancellationToken)
        {
            return ValueTask.FromResult(GetToken(requestContext, cancellationToken));
        }
    }

    private sealed class StubHttpMessageHandler(
        Func<HttpRequestMessage, CancellationToken, Task<HttpResponseMessage>> sendAsync)
        : HttpMessageHandler
    {
        public int CallCount { get; private set; }

        protected override Task<HttpResponseMessage> SendAsync(
            HttpRequestMessage request,
            CancellationToken cancellationToken)
        {
            CallCount++;
            return sendAsync(request, cancellationToken);
        }
    }
}