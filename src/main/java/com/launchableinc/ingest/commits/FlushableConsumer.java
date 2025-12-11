package com.launchableinc.ingest.commits;

import java.io.Closeable;
import java.io.IOException;
import java.util.function.Consumer;

/**
 * Consumers that spool items it accepts and process them in bulk.
 */
public interface FlushableConsumer<T> extends Consumer<T>, Closeable {
  /**
   * Process all items that have been accepted so far.
   */
  void flush() throws IOException;

  static <T> FlushableConsumer<T> of(Consumer<T> c) {
    return new FlushableConsumer<T>() {
      @Override
      public void flush() {
        // noop
      }

      @Override
      public void close() {
        // noop
      }

      @Override
      public void accept(T t) {
        c.accept(t);
      }
    };
  }
}
