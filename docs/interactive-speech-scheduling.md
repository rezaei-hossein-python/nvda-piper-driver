# Interactive speech scheduling

Status: Experimental Phase 2L.

The prior controller used one replaceable pending slot and the driver stopped
the player for every request. That is appropriate for focus, navigation, and
mouse-over, but collapses rapid character events. The experiment distinguishes
character, navigation, and ordered requests: characters use an eight-entry
FIFO, navigation remains newest-wins, and Read All/ordinary speech retain
Phase 2K ordering.
