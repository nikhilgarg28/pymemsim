import math
from .block import Block

class Store(object):
    def __init__(self, name, num_blocks, block_size, num_cycles,
                 assoc=None, write_through=True, next_store=None,
                 tracker=None):
        self.name = name
        self.num_blocks = num_blocks
        self.block_size = block_size
        self._n_offset = int(math.log2(self.block_size))
        self.assoc = assoc
        if assoc is None:
            self.num_sets = 1
        else:
            self.num_sets = num_blocks // assoc
        self._n_set = int(math.log2(self.num_sets))

        # assuming a 32 bit address space
        self._n_tag = 32 - self._n_offset - self._n_set

        self.num_blocks_per_set = self.num_blocks // self.num_sets

        self.num_cycles = num_cycles

        self.next_store = next_store

        self.write_through = write_through
        self.tracker = tracker

        self._flush()

    def _flush(self):
        """Remove all data from the store."""
        self._d = {}
        for s in range(self.num_sets):
            self._d[s] = [(None, None) for _ in range(self.num_blocks_per_set)]

    def read(self, addr, size):
        """Reads size bytes starting at address addr."""
        ret = []

        loop = True
        while loop:
            _, _, offset = self._decompose(addr)
            block = self._load_block(addr)
            buf = block.buf

            n_read = self.block_size - offset
            if n_read < size:
                addr, size = addr + n_read, size - n_read
                this = buf[offset:]
            else:
                this = buf[offset:offset+size]
                loop = False

            ret.extend(this)

        if len(ret) == 1:
            return ret[0]
        return ret

    def _load_block(self, addr):
        """Returns the block containing addr.

        If the block is not present, it calls read on the next level store.

        """
        ret_block = None

        tag, set_index, offset = self._decompose(addr)
        block_list = self._d[set_index]
        for tag_, block in block_list:
            if tag == tag_:
                self._track(addr, read=True, hit=True)
                return block

        # block not present, so mark as miss...
        self._track(addr, read=True, hit=False)

        # ...and load from the next level of the store
        block_base = addr - offset
        block = self._read_block_from_next(block_base)

        # and add it to the store
        self._write_block(addr, block)

        return block

    def _write_block(self, addr, block):
        """Writes the block containing addr."""
        self._track(addr, read=False)
        tag, set_index, offset = self._decompose(addr)
        block_list = self._d[set_index]
        for i, entry in enumerate(block_list):
            tag_, _ = entry
            if tag_ is None:
                block_list[i] = (tag, block)
                return

        # no empty slot, so need to evict a block
        index = self._evict_from(block_list)
        block_list[index] = (tag, block)

    def _evict_from(self, block_list):
        best_index, oldest_timestamp = None, None
        for i, entry in enumerate(block_list):
            _, block = entry
            if (oldest_timestamp is None) or block.timestamp < oldest_timestamp:
                best_index, oldest_timestamp = i, block.timestamp

        _, block_to_evict = block_list[best_index]
        if block_to_evict.dirty:
            assert self.write_through

            self._write_block_to_next(block)

        return best_index

    def _write_block_to_next(block):
        # TODO
        pass

    def _read_block_from_next(self, base):
        if self.next_store is None:
            buf = [0] * self.block_size
        else:
            buf = self.next_store.read(base, self.block_size)
        return Block(self.block_size, base, buf)

    def _decompose(self, addr):
        offset = _get_bits(addr, self._n_offset, 0)
        set_index = _get_bits(addr, self._n_set, self._n_offset)
        tag = _get_bits(addr, self._n_tag, self._n_offset + self._n_set)
        return tag, set_index, offset

    def _track(self, addr, read, hit=None):
        if self.tracker:
            self.tracker.track(self.name, addr, read, self.num_cycles, hit)

    def write(self, addr, buf):
        _, _, offset = self._decompose(addr)
        block = self._load_block(addr)
        block.write(addr, buf)

        # this might not be required?
        self._write_block(addr, block)

def _get_bits(addr, n_bits, to_discard):
    addr = addr >> to_discard
    mask = (1 << n_bits) - 1
    return addr & mask
