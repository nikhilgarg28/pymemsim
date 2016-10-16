import pymemsim
from pymemsim import Store


class TestStore(object):
    def setup(self):
        self.t = pymemsim.Tracker()

    def get_many_stores(self):
        return [
            # fully associative, write through, no backing
            Store('test', 1, 2, 1, tracker=self.t),

            # 2-set associative, write through, with no backing
            Store('test', 2, 2, 1, assoc=2, tracker=self.t),
        ]

    def test_read_write(self):
        for s in self.get_many_stores():
            s.write(0, [1, 2])
            assert 1 == s.read(0, 1)
            assert 2 == s.read(1, 1)
            assert [1, 2] == s.read(0, 2)
