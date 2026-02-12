package com.launchableinc.ingest.commits;

import org.apache.http.entity.ContentProducer;

import java.io.IOException;
import java.io.OutputStream;
import java.io.UncheckedIOException;
import java.util.ArrayList;
import java.util.List;

/**
 * Accepts T, buffers them, and writes them out as a batch.
 */
abstract class ChunkStreamer<T> implements FlushableConsumer<T> {
  /**
   * Encapsulation of how batches are sent.
   */
  private final IOConsumer<ContentProducer> sender;
  private final int chunkSize;
  private List<T> spool = new ArrayList<>();

  ChunkStreamer(IOConsumer<ContentProducer> sender, int chunkSize) {
    this.sender = sender;
    this.chunkSize = chunkSize;
  }

  @Override
  public void accept(T f) {
    spool.add(f);
    if (spool.size() >= chunkSize) {
      try {
        flush();
      } catch (IOException e) {
        throw new UncheckedIOException(e);
      }
    }
  }

  @Override
  public void close() throws IOException {
    flush();
  }

  @Override
  public void flush() throws IOException {
    if (spool.isEmpty()) {
      return;
    }

    // let sender own the list -- do not reuse
    // for this to work, we need to resolve `this.spool` here, not in the lambda
    List<T> ref = this.spool;
    this.spool = new ArrayList<>();

    sender.accept(os -> writeTo(ref,os));
  }

  protected abstract void writeTo(List<T> spool, OutputStream os) throws IOException;
}
