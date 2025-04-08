using ConferencePlanner.GraphQL.Data;
using ConferencePlanner.GraphQL.Models;
using Microsoft.EntityFrameworkCore;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddCors(options => 
{
    options.AddPolicy("AllowAll", policy =>
    {
        policy.AllowAnyOrigin()
            .AllowAnyMethod()
            .AllowAnyHeader();
    });
});

builder.Services
    .AddDbContext<ApplicationDbContext>(
        options => options.UseNpgsql("Host=127.0.0.1;Username=graphql_workshop;Password=secret"))
    .AddSingleton<IBackgroundTaskQueue, BackgroundTaskQueue>()
    .AddHostedService<BackgroundWorker>()
    .AddGraphQLServer()
    .AddGraphQLTypes();

var app = builder.Build();

app.UseCors("AllowAll");

app.MapGraphQL();

await app.RunWithGraphQLCommandsAsync(args);