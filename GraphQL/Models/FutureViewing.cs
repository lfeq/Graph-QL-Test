using System.ComponentModel.DataAnnotations;

namespace ConferencePlanner.GraphQL.Models;

public class FutureViewing {
    public Guid Id { get; set; }
    
    [StringLength(200)]
    public required string Name { get; set; }
    
    public required int Age { get; set; }
    
    [StringLength(4000)]
    public required string Content { get; set; }
    
    public DateTime CreatedAt { get; set; }
    
    public string? ImageUrl { get; set; }
}