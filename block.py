# TODO: add support for sparse buffer
# TODO: add support for buffer where we don't store the actual data

_time = 0


def now():
    global _time
    _time += 1
    return _time


class Block(object):
    def __init__(self, block_size, base, buf):
        self.block_size = block_size
        self.base = base
        self.buf = buf

        self.dirty = False
        self.timestamp = None

    def __str__(self):
        return str(self.buf)

    def __repr(self):
        return str(self.buf)

    def touch(self):
        self.timestamp = now()

    def read(self, offset=0, size=None):
        if size is None:
            size = self.block_size
        return self.buf[offset:size]

    def write(self, offset, buf):
        assert offset + len(buf) <= self.block_size
        for i, b in enumerate(buf):
            self.buf[i+offset] = buf[i]
