# Phase 2K portable validation

Status: Proposed

Portable validation must use `D:\NVDA` with all other NVDA instances closed. Compare Piper and eSpeak for first speech, slow/rapid characters, words, character/word/line navigation, focus changes, replacement, edit-box entry/exit, Read All, cancellation, switching, and shutdown.

Automated bridge measurements do not replace physical audible-onset measurements. Record only categories, timings, worker state, request IDs, generations, PCM sizes, and cancellation state; never record speech or document text.

The restored-model automated gate passed 104 source and archive tests with no failures. Two clean SCons builds produced the same 11 archive members and identical per-member SHA-256 content hashes. Portable interaction, audible onset, and subjective Piper-versus-eSpeak comparison remain user-run steps.
