using ConferencePlanner.GraphQL.Models;
using Microsoft.EntityFrameworkCore;

namespace ConferencePlanner.GraphQL.Data;

public static class Queries
{
    [Query]
    public static async Task<IEnumerable<Speaker>> GetSpeakersAsync(
        ApplicationDbContext dbContext,
        CancellationToken cancellationToken)
    {
        return await dbContext.Speakers.AsNoTracking().ToListAsync(cancellationToken);
    }
    
    [Query]
    public static async Task<IEnumerable<FutureViewing>> GetFutureViewingsAsync(
        ApplicationDbContext dbContext,
        CancellationToken cancellationToken)
    {
        return await dbContext.FutureViewings.AsNoTracking().ToListAsync(cancellationToken);
    }
}