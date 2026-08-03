# Mouse-over and focus scheduling

Short non-character requests use the existing newest-wins generation policy.
A new focus, Alt+Tab, control, or mouse-over request invalidates queued
character events and stale audio; the driver stops local playback before
submission. No arbitrary document text is cached.
