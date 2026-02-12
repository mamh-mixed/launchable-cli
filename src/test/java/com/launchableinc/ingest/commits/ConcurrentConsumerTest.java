package com.launchableinc.ingest.commits;

import org.junit.Test;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicInteger;

import static com.google.common.truth.Truth.assertThat;
import static org.junit.Assert.fail;

public class ConcurrentConsumerTest {
  @Test
  public void basicProcessing() throws IOException {
    ExecutorService executor = Executors.newFixedThreadPool(2);
    List<Integer> processed = Collections.synchronizedList(new ArrayList<>());

    try (ConcurrentConsumer<Integer> consumer = new ConcurrentConsumer<>(processed::add, executor)) {
      consumer.accept(1);
      consumer.accept(2);
      consumer.accept(3);
    } finally {
      executor.shutdown();
    }

    assertThat(processed.size()).isEqualTo(3);
    assertThat(processed).contains(1);
    assertThat(processed).contains(2);
    assertThat(processed).contains(3);
  }

  @Test
  public void concurrentProcessing() throws IOException, InterruptedException {
    ExecutorService executor = Executors.newFixedThreadPool(3);
    CountDownLatch latch = new CountDownLatch(3);
    AtomicInteger concurrentCount = new AtomicInteger(0);
    AtomicInteger maxConcurrent = new AtomicInteger(0);

    IOConsumer<Integer> slowConsumer = (i) -> {
      try {
        int current = concurrentCount.incrementAndGet();
        maxConcurrent.updateAndGet(max -> Math.max(max, current));
        latch.countDown();

        // Wait for all three to be running concurrently
        latch.await();
        Thread.sleep(50);
        concurrentCount.decrementAndGet();
      } catch (InterruptedException e) {
        throw new RuntimeException(e);
      }
    };

    try (ConcurrentConsumer<Integer> consumer = new ConcurrentConsumer<>(slowConsumer, executor)) {
      consumer.accept(1);
      consumer.accept(2);
      consumer.accept(3);
    } finally {
      executor.shutdown();
    }

    assertThat(maxConcurrent.get()).isEqualTo(3);
  }

  @Test
  public void exceptionPropagation() {
    ExecutorService executor = Executors.newFixedThreadPool(2);

    IOConsumer<Integer> throwingConsumer = (i) -> {
      if (i == 2) {
        throw new IOException("Test exception");
      }
    };

    ConcurrentConsumer<Integer> consumer = new ConcurrentConsumer<>(throwingConsumer, executor);
    consumer.accept(1);
    consumer.accept(2);
    consumer.accept(3);

    // Expected - exception should be thrown on close
    try {
      consumer.close();
      fail("Expected IOException was not thrown");
    } catch (IOException e) {
      assertThat(e.getMessage()).contains("Test exception");
    } finally {
      executor.shutdown();
    }
  }

  @Test
  public void closeWaitsForCompletion() throws IOException {
    ExecutorService executor = Executors.newFixedThreadPool(2);
    AtomicInteger completed = new AtomicInteger(0);

    IOConsumer<Integer> slowConsumer = (i) -> {
      try {
        Thread.sleep(100);
        completed.incrementAndGet();
      } catch (InterruptedException e) {
        throw new RuntimeException(e);
      }
    };

    try (ConcurrentConsumer<Integer> consumer = new ConcurrentConsumer<>(slowConsumer, executor)) {
      consumer.accept(1);
      consumer.accept(2);
      consumer.accept(3);

      // Items should still be processing
      assertThat(completed.get()).isLessThan(3);
    } finally {
      executor.shutdown();
    }

    // After close(), all items should be completed
    assertThat(completed.get()).isEqualTo(3);
  }
}
