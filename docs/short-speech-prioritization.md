# Short-speech prioritization

The Phase 2K controller remains bounded to one active request and one newest
pending request. Generation invalidation makes a newer character or
navigation request supersede stale output without reordering commands inside a
single NVDA speech sequence. Read All remains interruptible and uses the same
controller. The Phase 2L experiment does not introduce a second queue or speech
framework.
