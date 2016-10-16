__doc__ = """

Module that contains the core logic of hierarchical stores.

This is the protocol for lower level stores talk to higher level stores:

    Read:
        check data in store
        if present: return
        if not:
            recursively read it from higher score
            find an open slot to store the data
            if found: store and return
            else: evict an item (based on LRU), store and return

    Write:
        read data in store
        modify it in store
        if write through:
            recursively write to higher store


"""

import math
from .block import Block


class SegFault(Exception):
    def __init__(self, addr):
        self.addr = addr


class Store(object):
    def __init__(self, name, num_blocks, block_size, num_cycles,
                 assoc=None, write_through=False, next_store=None,
                 tracker=None, implicit=False):
        self.name = name
        self.block_size = block_size
        self._n_offset = int(math.log2(self.block_size))
        self.num_blocks = num_blocks
        self.assoc = assoc
        if assoc is None:
            self.num_sets = 1
        else:
            self.num_sets = num_blocks // assoc
        self._n_set = int(math.log2(self.num_sets))

        # assuming a 64 bit address space
        self._n_tag = 64 - self._n_offset - self._n_set

        self.num_blocks_per_set = self.num_blocks // self.num_sets

        self.num_cycles = num_cycles

        self.next_store = next_store

        self.write_through = write_through
        self.tracker = tracker
        self.implicit = implicit

        self._flush()

    def _flush(self):
        """Remove all data from the store."""
        self._d = {}

    def read(self, addr, size):
        """Reads size bytes starting at address addr."""
        ret = []

        while size > 0:
            block = self._load_block(addr)
            offset = addr - block.base
            n_read = self.block_size - offset

            less = size if size < n_read else n_read
            end = offset + less
            addr += n_read
            size -= n_read
            this = block.read(offset, end)

            if not ret:
                ret = this
            else:
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

        if set_index not in self._d:
            self._d[set_index] = []
        block_list = self._d[set_index]
        for tag_, block in block_list:
            if tag == tag_:
                self._track(addr, read=True, hit=True)
                return block

        # block not explicitly present, so might be a miss
        if self.implicit and len(block_list) <= self.num_blocks_per_set:
            # even though the addr hasn't been explicitly added to the store
            # yet, this store is implicity known to have been zerod out
            # so we just create a new block and store it explicitly, and
            # pretend it was a hit
            self._track(addr, read=True, hit=True)
            base = addr - offset
            block = Block(self.block_size, base)
            block_list.append((tag, block))
            return block

        # definite miss
        self._track(addr, read=True, hit=False)

        # ...and load from the next level of the store
        block_base = addr - offset
        block = self._read_block_from_next(block_base)

        # and add it to the store
        self._write_block(addr, block, direct=False)

        return block

    def _write_block(self, addr, block, direct=True):
        """Writes the block containing addr."""
        self._track(addr, read=False)
        tag, set_index, offset = self._decompose(addr)
        if set_index not in self._d:
            self._d[set_index] = []
        block_list = self._d[set_index]

        inserted = False
        for i, entry in enumerate(block_list):
            tag_, _ = entry
            if tag_ == tag:
                block_list[i] = (tag, block)
                inserted = True
                break

        if not inserted:
            if len(block_list) < self.num_blocks_per_set:
                block_list.append((tag, block))
            else:
                # no empty slot, so need to evict a block
                index = self._evict_from(block_list)
                block_list[index] = (tag, block)

        # also write to next store if in write-through mode
        if direct and self.write_through:
            base = addr - offset
            self._write_block_to_next(base, block)

    def _evict_from(self, block_list):
        best_index, oldest_timestamp = None, None
        for i, entry in enumerate(block_list):
            _, block = entry
            if (oldest_timestamp is None) or block.timestamp < oldest_timestamp:
                best_index, oldest_timestamp = i, block.timestamp

        _, block_to_evict = block_list[best_index]
        if block_to_evict.dirty:
            #assert self.write_through or (self.next_store is None)
            self._write_block_to_next(block.base, block)

        return best_index

    def _write_block_to_next(self, base, block):
        # TODO: since our stores are "inclusive", so that every cache line is
        # that's present in this store is also present in next store
        # when writing data to next store, processor doesn't have to read it again
        # but the simulator doesn't simulate that yet, and this is one (of
        # many) source of over-estimates
        if self.next_store is not None:
            self.next_store.write(base, block.buf)
        block.commit()

    def _read_block_from_next(self, base):
        if self.next_store is None:
            raise SegFault(base)
        else:
            buf = self.next_store.read(base, self.block_size)
        return Block(self.block_size, base, buf)

    def _decompose(self, addr):
        offset = addr & ((1 << self._n_offset) - 1)
        addr = addr >> self._n_offset

        set_index = addr & ((1 << self._n_set) - 1)
        addr = addr >> self._n_set

        return addr, set_index, offset

    def _track(self, addr, read, hit=None):
        if self.tracker:
            self.tracker.track(self.name, addr, read, self.num_cycles, hit)

    def write(self, addr, buf):
        while buf:
            block = self._load_block(addr)
            offset = addr - block.base
            n_write = self.block_size - offset

            block.write(offset, buf[:n_write])
            self._write_block(addr, block)
            addr += n_write
            buf = buf[n_write:]
