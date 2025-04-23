using ConferencePlanner.GraphQL.Models;
using DotNetEnv;
using OpenAI;
using OpenAI.Images;
using Path = System.IO.Path;

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
            Status = ProcessingStatus.Pending, // Nuevo campo de estado
            HasBeenViewed = false // Nuevo campo de visualización
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
                var options = new ImageGenerationOptions {
                    Size = GeneratedImageSize.W1024xH1024,
                    ResponseFormat = GeneratedImageFormat.Bytes
                };
                var prompt = $"Imagen para {input.Name} ({input.Age} años): {input.Content}";
                GeneratedImage image =
                    await client.GenerateImageAsync(prompt: prompt, cancellationToken: ct, options: options);
                var imageBytes = image.ImageBytes;

                // Actualizar registro con la imagen
                var entry = await db.FutureViewings.FindAsync(futureViewing.Id, ct);
                entry.Status = ProcessingStatus.Completed;
                string fileName = $"{entry.Id}.png";
                string imagesDirectory = Path.Combine(Directory.GetCurrentDirectory(),"wwwroot", "images");
                await db.SaveChangesAsync(ct);
                if (!Directory.Exists(imagesDirectory)) {
                    Directory.CreateDirectory(imagesDirectory);
                }
                string filePath = Path.Combine(imagesDirectory, fileName);
                await File.WriteAllBytesAsync(filePath, imageBytes, ct);
                entry.ImageUrl = $"images/{fileName}";
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