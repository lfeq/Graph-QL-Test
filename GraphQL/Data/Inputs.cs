namespace ConferencePlanner.GraphQL.Data;

public sealed record Inputs(
    string Name,
    string? Bio,
    string? Website
);

public sealed record AddFutureViewingInput(
    string Name,
    int Age,
    string Content
);