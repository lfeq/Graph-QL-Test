using System.Threading.Channels;

namespace ConferencePlanner.GraphQL.Models;

public interface IBackgroundTaskQueue {
    void Enqueue(Func<IServiceProvider, CancellationToken, Task> task);
    Task<Func<IServiceProvider, CancellationToken, Task>> DequeueAsync(CancellationToken ct);
}

public class BackgroundTaskQueue : IBackgroundTaskQueue {
    private readonly Channel<Func<IServiceProvider, CancellationToken, Task>> _queue;

    public BackgroundTaskQueue() {
        var options = new BoundedChannelOptions(100) {
            FullMode = BoundedChannelFullMode.Wait
        };
        _queue = Channel.CreateBounded<Func<IServiceProvider, CancellationToken, Task>>(options);
    }

    public void Enqueue(Func<IServiceProvider, CancellationToken, Task> task) 
        => _queue.Writer.TryWrite(task);

    public async Task<Func<IServiceProvider, CancellationToken, Task>> DequeueAsync(CancellationToken ct) 
        => await _queue.Reader.ReadAsync(ct);
}

public class BackgroundWorker : BackgroundService {
    private readonly IBackgroundTaskQueue _taskQueue;
    private readonly IServiceProvider _services;

    public BackgroundWorker(IBackgroundTaskQueue taskQueue, IServiceProvider services) {
        _taskQueue = taskQueue;
        _services = services;
    }

    protected override async Task ExecuteAsync(CancellationToken ct) {
        while (!ct.IsCancellationRequested) {
            var task = await _taskQueue.DequeueAsync(ct);
            await task(_services, ct);
        }
    }
}