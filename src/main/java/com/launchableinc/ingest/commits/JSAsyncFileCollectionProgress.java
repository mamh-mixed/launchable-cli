package com.launchableinc.ingest.commits;

import com.fasterxml.jackson.annotation.JsonProperty;

public class JSAsyncFileCollectionProgress {
  @JsonProperty
  public BackgroundWorkStatus status;
  @JsonProperty
  public int filesProcessed;
}
