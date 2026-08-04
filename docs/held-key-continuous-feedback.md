# Held-key continuous feedback

The held loop enters only after identical character-mode events arrive while a
character request is active and within the measured repeat window (150 ms in
the development prototype). It replays the already validated cached PCM
without worker calls. When no repeat arrives for the window, the loop exits and
does not drain an obsolete backlog.

The implementation is deliberately opt-in. Portable testing must establish
whether full natural character clips provide useful continuous feedback or are
too long for the target repeat cadence.
