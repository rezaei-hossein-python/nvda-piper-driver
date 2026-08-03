# Repeated-character event fidelity

Repeated requests are identified by generation and job identity, not speech
content. Identical cached PCM may be reused, but each accepted keypress has a
separate playback lifecycle. At most eight character events may be pending;
additional events are explicitly counted as dropped. Cancellation clears the
FIFO. Portable validation remains required.
