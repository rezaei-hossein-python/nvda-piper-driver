# Character audio looping

The prototype uses the existing `nvwave.WavePlayer` and omits `idle()` between
consecutive loop clips while the opt-in held loop is active. Ordinary speech
continues to use the existing drain behavior. Navigation and focus retain
preemption through the current controller and local player stop path.

No waveform slicing, crossfade, gap synthesis, or second audio device was
introduced. Such changes require separate PCM-boundary measurements.
