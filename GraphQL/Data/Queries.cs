using ConferencePlanner.GraphQL.Models;
using Microsoft.EntityFrameworkCore;

namespace ConferencePlanner.GraphQL.Data;

public static class Queries {
    [Query]
    public static async Task<IEnumerable<Speaker>> GetSpeakersAsync(
        ApplicationDbContext dbContext,
        CancellationToken cancellationToken) {
        return await dbContext.Speakers.AsNoTracking().ToListAsync(cancellationToken);
    }

    [Query]
    public static async Task<IEnumerable<FutureViewing>> GetFutureViewingsAsync(
        ApplicationDbContext dbContext,
        int page = 1, // Default to the first page
        int pageSize = 20, // Set the page size to 20
        CancellationToken cancellationToken = default) {
        if (page <= 0) {
            page = 1; // Ensure page number is at least 1
        }
        if (pageSize <= 0) {
            pageSize = 20; // Ensure page size is at least 1
        }
        return await dbContext.FutureViewings
            .OrderByDescending(f => f.CreatedAt)
            .Skip((page - 1) * pageSize) // Skip the appropriate number of records
            .Take(pageSize) // Take only the specified number of records
            .AsNoTracking()
            .ToListAsync(cancellationToken);
    }

    [Query]
    public static async Task<IEnumerable<FutureViewing>> GetRecentFutureViewingsAsync(
        ApplicationDbContext dbContext,
        int page = 1, // Default to the first page
        int pageSize = 20, // Set the page size to 20
        CancellationToken cancellationToken = default) {
        if (page <= 0) {
            page = 1; // Ensure page number is at least 1
        }
        if (pageSize <= 0) {
            pageSize = 20; // Ensure page size is at least 1
        }

        // Calculate the date and time 24 hours ago
        DateTime twentyFourHoursAgo = DateTime.UtcNow.AddHours(-24);
        List<FutureViewing> imagesToShow = await dbContext.FutureViewings
            .Where(x => x.Status == ProcessingStatus.Completed && x.CreatedAt >= twentyFourHoursAgo && !x.HasBeenViewed)
            .OrderByDescending(f => f.CreatedAt)
            .Skip((page - 1) * pageSize) // Skip the appropriate number of records
            .Take(pageSize) // Take only the specified number of records
            .ToListAsync(cancellationToken);
        // revert imagetstoshow
        imagesToShow.Reverse();
        foreach (FutureViewing image in imagesToShow) {
            image.HasBeenViewed = true;
        }
        await dbContext.SaveChangesAsync(cancellationToken);
        return imagesToShow;
    }
}