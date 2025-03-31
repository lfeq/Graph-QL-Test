using ConferencePlanner.GraphQL.Models;
using DotNetEnv;
using OpenAI;
using OpenAI.Images;

namespace ConferencePlanner.GraphQL.Data;

public static class Mutations {
    [Mutation]
    public static async Task<Payloads> AddSpeakerAsync(
        Inputs input,
        ApplicationDbContext dbContext,
        CancellationToken cancellationToken) {
        var speaker = new Speaker {
            Name = input.Name,
            Bio = input.Bio,
            WebSite = input.Website
        };
        dbContext.Speakers.Add(speaker);
        await dbContext.SaveChangesAsync(cancellationToken);
        return new Payloads(speaker);
    }

    [Mutation]
    public static async Task<AddFutureViewingPayload> AddFutureViewingAsync(
        AddFutureViewingInput input,
        ApplicationDbContext dbContext,
        CancellationToken cancellationToken) {
        Env.Load();
        
        ImageClient client = new(
            model: "dall-e-3",
            apiKey: Environment.GetEnvironmentVariable("OPENAI_API_KEY")
        );
        var prompt =
            $"Una imagen imaginando un mundo por una persona llamada {input.Name} de {input.Age} años de edad y " +
            $"se imagina el mundo de la siguiente forma {input.Content}";
        GeneratedImage image = await client.GenerateImageAsync(prompt: prompt, cancellationToken: cancellationToken);
        
        var futureViewing = new FutureViewing {
            Name = input.Name,
            Age = input.Age,
            Content = input.Content,
            CreatedAt = DateTime.UtcNow,
            ImageUrl = image.ImageUri.ToString()
        };
        dbContext.FutureViewings.Add(futureViewing);
        await dbContext.SaveChangesAsync(cancellationToken);
        return new AddFutureViewingPayload(futureViewing);
    }
}