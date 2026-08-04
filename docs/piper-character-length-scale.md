# Piper character length scale

Length-scale variants are generated only for character-mode cache misses. The
worker creates a separate bounded `SynthesisConfig` for characters while
ordinary requests use the existing warm configuration. Invalid or absent
factors fall back to normal scale 1.0. Cache keys include the selected factor.
