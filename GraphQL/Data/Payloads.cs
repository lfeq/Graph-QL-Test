using ConferencePlanner.GraphQL.Models;

namespace ConferencePlanner.GraphQL;

public sealed class Payloads(Speaker speaker) {
    public Speaker Speaker { get; } = speaker;
}

public sealed class AddFutureViewingPayload (FutureViewing futureViewing){
    public FutureViewing futureViewing { get; } = futureViewing;
}