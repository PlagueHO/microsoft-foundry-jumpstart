using System.Text.Json.Serialization;

namespace ImageGenerationExplorer.Models;

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

internal sealed class OpenAiImageGenerationRequestDto
{
    [JsonPropertyName("model")]
    public required string Model { get; init; }

    [JsonPropertyName("prompt")]
    public required string Prompt { get; init; }

    [JsonPropertyName("size")]
    public required string Size { get; init; }

    [JsonPropertyName("n")]
    public int N { get; init; } = 1;

    [JsonPropertyName("output_format")]
    public string OutputFormat { get; init; } = "png";

    [JsonPropertyName("output_compression")]
    public int OutputCompression { get; init; } = 100;
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
