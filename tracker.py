from collections import defaultdict
import pyutils.timekeeper

timekeeper = pyutils.timekeeper.TimeKeeper()

class Tracker(object):
    def __init__(self, detailed=False, verbose=False):
        self.clear()
        self.verbose = verbose
        self.detailed = detailed

    def clear(self):
        self.num_cycles = 0
        self.events = []
        self.sources = defaultdict(int)

    def track(self, name, addr, read, num_cycles, hit=None):
        self.sources[name] += num_cycles
        self.num_cycles += num_cycles

        if self.detailed:
            self.events.append((name, addr, read, hit))
        if not self.verbose:
            return
        if read:
            print('Reading data at address %s from %s. Took %d cycles and got a %s.' % (
                addr, name, num_cycles, 'hit' if hit else 'miss'
            ))
        else:
            print('Writing data at address %s in %s. Took %d cycles.' % (
                addr, name, num_cycles
            ))

    def get_num_cycles(self):
        return self.num_cycles
