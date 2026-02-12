package com.launchableinc.ingest.commits;

import java.io.Closeable;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Future;
import java.util.function.Consumer;

/**
 * A decorator of {@link IOConsumer}/{@link Consumer} that concurrently/asynchronously processes accepted items.
 * <p>
 * {@link #close()} method would wait for all the processing to complete, and fail if any of them throw an exception.
 */
class ConcurrentConsumer<T> implements IOConsumer<T>, Consumer<T>, Closeable {
  private final IOConsumer<T> delegate;
  private final ExecutorService executor;
  private final List<Future<?>> jobs = new ArrayList<>();

  ConcurrentConsumer(IOConsumer<T> delegate, ExecutorService executor) {
    this.delegate = delegate;
    this.executor = executor;
  }

  @Override
  public void accept(T t) {
    jobs.add(executor.submit(() -> {
      delegate.accept(t);
      return null; // to use Callable interface so as not to wrap an exception
    }));
  }

  @Override
  public void close() throws IOException {
    try {
      for (Future<?> job : jobs) {
        job.get();
      }
    } catch (InterruptedException|ExecutionException e) {
      throw new IOException(e);
    }
  }
}
