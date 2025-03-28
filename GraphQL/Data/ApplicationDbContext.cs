using ConferencePlanner.GraphQL.Models;
using Microsoft.EntityFrameworkCore;

namespace ConferencePlanner.GraphQL.Data;

public sealed class ApplicationDbContext(DbContextOptions<ApplicationDbContext> options)
    : DbContext(options)
{
    public DbSet<Speaker> Speakers { get; init; }
    public DbSet<FutureViewing> FutureViewings { get; init; }
}