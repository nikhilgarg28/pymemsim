from .block import Block
from .tracker import Tracker
from .cache import Store

"""Returns a store analogous to L1 cache.

The configuration of various caches is based on information from following
places:

    Specification for various caches are mashup from the following places:
    http://www.7-cpu.com/cpu/Haswell.html
    https://gist.github.com/jboner/2841832
    http://lwn.net/Articles/252125/

"""

tracker = Tracker()

# RAM : "infinite size", block size 8 byes (64 bit arch), directly mapped,
# refrence takes around 300 cycles
RAM = Store('DRAM', None, 8, 300, tracker=tracker)

# L3 : 8MB, cache line 64B, directly mapped(?), refrence takes ~30 cycles
L3 = Store('L3', 1 << 17, 64, 30, assoc=1, tracker=tracker, next_store=RAM)

# L2 : 8MB, cache line 64B, 8-way, reference takes 12 cycles
L2 = Store('L2', 1 << 12, 64, 12, assoc=8, tracker=tracker, next_store=L3)

# L1 : 8MB, cache line 64B, 8-way, reference takes 12 cycles
L1 = Store('L1', 1 << 9, 64, 4, assoc=8, tracker=tracker, next_store=L2)

memory = L1
