# Phase 2L workerCrash stabilization

The Package C portable log recorded four `workerCrash` messages during
ordinary replacement/cancellation. Source tracing showed the child was being
terminated by `PersistentRuntimeBridge.interrupt()` while the request thread
was blocked reading its response. Closing that pipe was converted to
`RuntimeBridgeError("workerCrash")` before the cancellation token was checked.

The minimal fix checks the token after reaping the process: if it changed, the
result is `RuntimeBridgeCancelled`, suppressing the controller error report.
Unexpected pipe closure with an unchanged token remains a genuine
`workerCrash`. This preserves failure detection while removing the cancellation
race false positive. A direct approved-model smoke test still produces valid
16 kHz PCM and stops cleanly.

The original portable log did not contain request IDs or worker PIDs, so its
four entries cannot be individually reconstructed beyond this
source-equivalent cancellation/pipe-race classification. The supplied
post-fix Package C log is clean, with no workerCrash or emptySpeech entries;
the older log is retained only as historical pre-fix evidence.
