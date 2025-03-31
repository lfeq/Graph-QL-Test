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
        [Service] IBackgroundTaskQueue taskQueue, // Cola de tareas en segundo plano
        CancellationToken cancellationToken) {
        // Guardar el registro inicial sin imagen
        var futureViewing = new FutureViewing {
            Name = input.Name,
            Age = input.Age,
            Content = input.Content,
            CreatedAt = DateTime.UtcNow,
            Status = ProcessingStatus.Pending // Nuevo campo de estado
        };
        dbContext.FutureViewings.Add(futureViewing);
        await dbContext.SaveChangesAsync(cancellationToken);

        // Encolar generación de imagen en segundo plano
        taskQueue.Enqueue(async (IServiceProvider serviceProvider, CancellationToken ct) => {
            using var scope = serviceProvider.CreateScope();
            var db = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();
            var client = new ImageClient(
                model: "dall-e-3",
                apiKey: Environment.GetEnvironmentVariable("OPENAI_API_KEY")
            );
            try {
                var prompt = $"Imagen para {input.Name} ({input.Age} años): {input.Content}";
                GeneratedImage image = await client.GenerateImageAsync(prompt: prompt, cancellationToken: ct);

                // Actualizar registro con la imagen
                var entry = await db.FutureViewings.FindAsync(futureViewing.Id);
                entry.ImageUrl = image.ImageUri.ToString();
                entry.Status = ProcessingStatus.Completed;
                await db.SaveChangesAsync(ct);
            }
            catch (Exception ex) {
                futureViewing.Status = ProcessingStatus.Failed;
                await db.SaveChangesAsync(ct);
                // Opcional: Loggear el error
            }
        });
        return new AddFutureViewingPayload(futureViewing);
    }
}