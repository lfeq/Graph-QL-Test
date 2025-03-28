using System.ComponentModel.DataAnnotations;

namespace ConferencePlanner.GraphQL.Data;

public class Speaker {
    public Guid Id { get; set; }
    
    [StringLength(200)]
    public required string Name { get; set; }
    
    [StringLength(4000)]
    public string? Bio { get; set; }
    
    [StringLength(1000)]
    public string? WebSite { get; set; }
}