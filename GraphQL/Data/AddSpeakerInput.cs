namespace ConferencePlanner.GraphQL.Data;

public sealed record AddSpeakerInput(
    string Name,
    string? Bio,
    string? Website);