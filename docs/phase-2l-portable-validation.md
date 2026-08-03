# Phase 2L portable A/B validation

Build the accepted Phase 2K package as control, and a separate copy for the
experimental package. Use disposable configs:

```text
D:\NVDA\phase2lControl
D:\NVDA\phase2lExperimental
```

The experimental launch must set both
`NVDA_PIPER_EXPERIMENTAL_SHORT_SPEECH=1` and
`NVDA_PIPER_EXPERIMENTAL_CACHE=1`. Compare repeated characters, Unicode and
punctuation, rapid replacement, navigation, cancellation, edit-box recovery,
Read All, and eSpeak switching. Do not interpret worker timings as physical
audible onset; record the user's portable observation separately.

This build's control archive SHA-256 is
`f1094490f7ba602690af961bc1b8948bf2ea380588a40def393f47e603aebfd9`; the
experimental archive SHA-256 is
`5cf983f2ad537c2c004d3dfad6e831204369ab33c92e2f635ad3ef6a8cfab04c`.
The approved model remains external and ignored. Direct warm-worker smoke
testing measured roughly 25–31 ms after the cold request; cache lookup is
memory-only and must be judged by first-feed metrics and portable listening.
