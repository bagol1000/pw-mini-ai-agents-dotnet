using System.Net.Http.Json;
using System.Text.Json;
using System.Text.Json.Serialization;

public sealed class OllamaClient(HttpClient http)
{
    private static readonly JsonSerializerOptions Options = new()
    {
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull
    };

    // format: null (zwykły tekst), "json" albo obiekt JSON Schema
    public async Task<string> GenerateAsync(
        string model,
        string prompt,
        double temperature = 0,
        object? format = null)
    {
        if (model == "gpt-6-luna")
        {
            var apiKey = Environment.GetEnvironmentVariable("OPENAI_API_KEY");

            if (string.IsNullOrWhiteSpace(apiKey))
                throw new InvalidOperationException("Brak OPENAI_API_KEY.");

            object? responseFormat = null;

            if (format is string formatName)
            {
                if (formatName != "json")
                    throw new ArgumentException("Nieobsługiwany format OpenAI.", nameof(format));

                responseFormat = new { type = "json_object" };
            }
            else if (format is not null)
            {
                var schema = System.Text.Json.Nodes.JsonNode.Parse(
                    JsonSerializer.Serialize(format))!;

                schema["additionalProperties"] = false;

                responseFormat = new
                {
                    type = "json_schema",
                    json_schema = new
                    {
                        name = "delivery_note",
                        strict = true,
                        schema
                    }
                };
            }

            var body = new
            {
                model,
                messages = new[]
                {
                    new { role = "user", content = prompt }
                },
                reasoning_effort = "none",
                temperature,
                response_format = responseFormat
            };

            using var apiRequest = new HttpRequestMessage(
                HttpMethod.Post,
                "https://api.openai.com/v1/chat/completions");

            apiRequest.Headers.Authorization =
                new System.Net.Http.Headers.AuthenticationHeaderValue("Bearer", apiKey);

            apiRequest.Content = JsonContent.Create(body, options: Options);

            using var apiResponse = await http.SendAsync(apiRequest);
            var responseBody = await apiResponse.Content.ReadAsStringAsync();

            if (!apiResponse.IsSuccessStatusCode)
                throw new HttpRequestException(
                    $"OpenAI HTTP {(int)apiResponse.StatusCode}: {responseBody}");

            using var document = JsonDocument.Parse(responseBody);

            return document.RootElement
                .GetProperty("choices")[0]
                .GetProperty("message")
                .GetProperty("content")
                .GetString() ?? "";
        }

        var request = new
        {
            model,
            messages = new[]
            {
                new { role = "user", content = prompt }
            },
            stream = false,
            format,
            options = new
            {
                temperature
            }
        };

        using var response = await http.PostAsJsonAsync(
            "http://localhost:11434/api/chat",
            request,
            Options);

        response.EnsureSuccessStatusCode();

        using var json = await response.Content
            .ReadFromJsonAsync<JsonDocument>();

        return json!.RootElement
            .GetProperty("message")
            .GetProperty("content")
            .GetString() ?? "";
    }
}
