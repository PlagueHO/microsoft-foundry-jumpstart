using System.Text.Json.Serialization;

namespace MaiImage2Simple.Models;

internal sealed class MaiImageGenerationRequestDto
{
    [JsonPropertyName("model")]
    public required string Model { get; init; }

    [JsonPropertyName("prompt")]
    public required string Prompt { get; init; }

    [JsonPropertyName("width")]
    public required int Width { get; init; }

    [JsonPropertyName("height")]
    public required int Height { get; init; }
}

internal sealed class MaiImageGenerationResponseDto
{
    [JsonPropertyName("data")]
    public List<MaiImageDataDto> Data { get; init; } = [];
}

internal sealed class MaiImageDataDto
{
    [JsonPropertyName("b64_json")]
    public string? Base64Json { get; init; }
}

internal sealed class MaiErrorEnvelopeDto
{
    [JsonPropertyName("error")]
    public MaiErrorDto? Error { get; init; }
}

internal sealed class MaiErrorDto
{
    [JsonPropertyName("message")]
    public string? Message { get; init; }

    [JsonPropertyName("code")]
    public string? Code { get; init; }
}