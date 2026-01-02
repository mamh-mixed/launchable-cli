package com.launchableinc.ingest.commits;

import java.util.List;
import java.util.concurrent.AbstractExecutorService;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.Semaphore;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * {@link ExecutorService} decorator that limits the number of concurrent tasks,
 * and make the caller block when the limit is reached.
 */
class BoundedExecutorService extends AbstractExecutorService {
  private final ExecutorService delegate;
  private final Semaphore semaphore;
  /** # of threads that are blocked trying to {@link #execute(Runnable)}. Just for diagnostics. */
  private final AtomicInteger blockCount = new AtomicInteger(0);

  BoundedExecutorService(int limit) {
    this(Executors.newFixedThreadPool(limit), limit);
  }

  BoundedExecutorService(ExecutorService delegate, int limit) {
    this.delegate = delegate;
    this.semaphore = new Semaphore(limit);
  }

  @Override
  public void execute(Runnable command) {
    try {
      blockCount.incrementAndGet();
      semaphore.acquire();
    } catch (InterruptedException e) {
      throw new RejectedExecutionException(e);
    } finally {
      blockCount.decrementAndGet();
    }

    try {
      delegate.execute(() -> {
        try {
          command.run();
        } finally {
          semaphore.release();
        }
      });
    } catch (RejectedExecutionException e) {
      semaphore.release();
      throw e;
    }
  }

  @Override
  public void shutdown() {
    delegate.shutdown();
  }

  @Override
  public List<Runnable> shutdownNow() {
    return delegate.shutdownNow();
  }

  @Override
  public boolean isShutdown() {
    return delegate.isShutdown();
  }

  @Override
  public boolean isTerminated() {
    return delegate.isTerminated();
  }

  @Override
  public boolean awaitTermination(long timeout, TimeUnit unit) throws InterruptedException {
    return delegate.awaitTermination(timeout, unit);
  }
}
