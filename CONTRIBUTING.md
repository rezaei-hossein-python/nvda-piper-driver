# Contributing

Thank you for considering a contribution to NVDA Piper Driver.

## Current stage

The project is in its research and architecture phase. Small, evidence-based contributions are preferred over broad implementations.

## Before contributing

1. Read `README.md`.
2. Read `AGENTS.md`.
3. Review the current roadmap and implementation plan.
4. Check existing issues and discussions before starting overlapping work.
5. Verify all NVDA-facing assumptions against the pinned NVDA source reference.

## Development workflow

1. Create a focused branch.
2. Make the smallest coherent change.
3. Add or update tests.
4. Update relevant documentation.
5. Run the applicable checks.
6. Explain design decisions and known limitations in the pull request.

## Pull-request expectations

A pull request should include:

- the problem being addressed;
- the chosen approach;
- files and interfaces affected;
- tests performed;
- accessibility impact;
- performance impact;
- licence or redistribution considerations for new dependencies;
- unresolved risks.

## Accessibility requirements

User-facing functionality must be operable with NVDA and the keyboard. Errors and settings must have meaningful names, states, and instructions.

## Dependencies and bundled assets

Do not add binaries, ONNX models, native libraries, or other third-party assets without documenting:

- upstream project and version;
- download source;
- checksum;
- licence;
- redistribution permission;
- supported architecture;
- update and security strategy.

## Privacy

Contributions must not introduce telemetry or collection of synthesized text, user activity, or speech content.

## Licence

By contributing, you agree that your contribution may be distributed under the repository's GPL-2.0-or-later licence.
