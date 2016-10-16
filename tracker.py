
class Tracker(object):
    def __init__(self, verbose=False):
        self.clear()
        self.verbose = verbose

    def clear(self):
        self.num_cycles = 0
        self.events = []
        self.sources = {}

    def track(self, name, addr, read, num_cycles, hit=None):
        self.num_cycles += num_cycles
        self.events.append((name, addr, read, hit))
        old = self.sources.get(name, 0)
        self.sources[name] = old + num_cycles
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
