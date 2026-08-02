# Phase 2H Piper component inventory

This inventory records local-experiment evidence as of 2026-08-01. It is not legal advice and authorizes no redistribution or add-on bundling.

| Component | Exact evidence | Source and licence | Architecture / acquisition | Redistribution classification |
|---|---|---|---|---|
| Piper runtime | `piper-tts` 1.5.0; Windows wheel SHA-256 `d05f0985143f180046d2765eed505a1f5ea1fc30cee4c9c18edb68ef58cce204` | OHF-Voice `piper1-gpl` tag `v1.5.0`; GPL-3.0-or-later; Home Assistant authors | CPython 3.9 ABI3, Windows x64; installed into a temporary venv from PyPI | Acceptable for local experimentation; future bundling requires GPL/source/notice review |
| Embedded eSpeak NG bridge/data | Included by Piper wheel; independent installed version not exposed | Piper describes embedded eSpeak NG; eSpeak NG is GPL-3.0-or-later | Native bridge and data inside the Piper wheel | Likely bundleable only with complete GPL and corresponding-source review |
| ONNX Runtime | 1.28.0 succeeded after the Visual C++ prerequisite was installed; `AzureExecutionProvider` and `CPUExecutionProvider` available; adapter used CPU | Microsoft ONNX Runtime; MIT | CPython 3.12 Windows x64 wheel from PyPI | Likely bundleable but wheel hash, native notices, provider policy, and servicing must be locked and reviewed |
| NumPy | 2.5.1 | NumPy project; BSD-3-Clause | Windows x64 wheel, temporary venv | Likely bundleable; transitive notices and wheel hash unresolved |
| pathvalidate | 3.3.1 | pathvalidate project; MIT | Pure Python wheel, temporary venv | Likely bundleable; not needed by the adapter directly and should be reviewed as Piper runtime closure |
| protobuf | 7.35.1 | Protocol Buffers project; BSD-3-Clause | Windows ABI3 wheel, temporary venv | Likely bundleable; exact need and notices unresolved |
| flatbuffers | 25.12.19 | Google FlatBuffers; Apache-2.0 | Pure Python wheel, temporary venv | Likely bundleable; notices unresolved |
| packaging | 26.2 | PyPA packaging; Apache-2.0 or BSD-2-Clause | Pure Python wheel, temporary venv | Likely bundleable; notices unresolved |
| Diagnostic ORT dependencies | coloredlogs 15.0.1, humanfriendly 10.0, pyreadline3 3.5.6, sympy 1.14.0, mpmath 1.3.0 | Upstream package metadata; mixed permissive licences | Appeared only in the unsuccessful earlier 1.23.2 diagnostic environment; absent from the successful 1.28.0 environment | Not part of the selected closure; retained as failure evidence |
| Microsoft Visual C++ runtime | Authenticode `Valid`, Microsoft Corporation; installer 18,731,856 bytes, SHA-256 `843068991daaa1f73ad9f6239bce4d0f6a07a51f18c37ea2a867e9beca71295c`; installed version 14.51.36247.0 | Microsoft permanent `vc14` x64 link and Microsoft Software License Terms | Interactive Windows x64 system prerequisite installation, exit code 0 | Not ready for add-on redistribution; central servicing, installer policy, and licence eligibility require review |
| Test voice | `en_US-lessac-low.onnx`; SHA-256 `f7d01dde371555732c4c314111ac79672b1a5ce2fc19266ab42178fd8df7f375` | `rhasspy/piper-voices`; repository declares MIT | Manually downloaded 63,201,294-byte ONNX model | Acceptable for local experimentation only; not approved for bundling |
| Voice configuration | `en_US-lessac-low.onnx.json`; SHA-256 `45754dfdebb3b8661c3fc564713772deec6e064feeb5b4e9594857dc7305193a` | Same voice repository and revision family | Manually downloaded 4,882-byte JSON | Follows test-voice status |
| Lessac Blizzard 2013 dataset | Referenced by the voice model card; no local dataset copy | University of Edinburgh/CSTR dataset page and separate Lessac Blizzard licence | Training provenance only | Unresolved for redistributed derived model; requires legal and voice-rights review |

The retained ignored environment also contains pip 26.2. It is an installation tool, not a runtime component. No component, model, binary, data file, or WAV is included in the NVDA add-on.
