package com.launchableinc.ingest.commits;

import org.junit.Test;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

import static com.google.common.truth.Truth.assertThat;
import static java.util.concurrent.TimeUnit.SECONDS;

public class BoundedExecutorServiceTest {
  @Test
  public void basicExecution() throws InterruptedException {
    BoundedExecutorService executor = new BoundedExecutorService(2);
    List<Integer> results = Collections.synchronizedList(new ArrayList<>());

    try {
      executor.execute(() -> results.add(1));
      executor.execute(() -> results.add(2));
      executor.execute(() -> results.add(3));
    } finally {
      executor.shutdown();
      executor.awaitTermination(5, SECONDS);
    }

    assertThat(results).containsExactly(1, 2, 3);
  }

  @Test
  public void enforcesConcurrencyLimit() throws InterruptedException {
    int limit = 2;
    BoundedExecutorService executor = new BoundedExecutorService(limit);
    CountDownLatch startLatch = new CountDownLatch(limit);
    CountDownLatch releaseLatch = new CountDownLatch(1);
    AtomicInteger concurrentCount = new AtomicInteger(0);
    AtomicInteger maxConcurrent = new AtomicInteger(0);
    AtomicInteger submittedCount = new AtomicInteger(0);

    Runnable task = () -> {
      try {
        int current = concurrentCount.incrementAndGet();
        maxConcurrent.updateAndGet(max -> Math.max(max, current));
        startLatch.countDown();
        releaseLatch.await();
        concurrentCount.decrementAndGet();
      } catch (InterruptedException e) {
        throw new RuntimeException(e);
      }
    };

    // Use a separate thread to sequentially submit tasks
    Thread submitter = new Thread(() -> {
      for (int i = 0; i < 4; i++) {
        executor.execute(task);
        submittedCount.incrementAndGet();
      }
    });

    try {
      submitter.start();

      // Wait for limit number of tasks to start
      startLatch.await(1, SECONDS);

      // Should have exactly 'limit' tasks running
      assertThat(concurrentCount.get()).isEqualTo(limit);

      // The submitter thread should be blocked trying to submit the 3rd task
      // Only 2 tasks should have been submitted successfully
      assertThat(submittedCount.get()).isEqualTo(2);

      // Release all tasks
      releaseLatch.countDown();

      // Wait for submitter to finish
      submitter.join(5000);
    } finally {
      executor.shutdown();
      executor.awaitTermination(5, SECONDS);
    }

    // Verify that concurrent execution never exceeded the limit
    assertThat(maxConcurrent.get()).isAtMost(limit);
    // All 4 tasks should have eventually been submitted
    assertThat(submittedCount.get()).isEqualTo(4);
  }
}
